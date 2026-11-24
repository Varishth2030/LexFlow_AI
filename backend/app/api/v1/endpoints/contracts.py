import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models import (
    AuditAction,
    AuditLog,
    Clause,
    Contract,
    ContractStatus,
    ContractType,
    DocumentChunk,
    Obligation,
    RiskAssessment,
    RiskSeverity,
    User,
)
from app.schemas.analysis import (
    ClauseResponse,
    ContractAnalysisResponse,
    ObligationListResponse,
    ObligationResponse,
    OrganizationObligationItemResponse,
    OrganizationObligationListResponse,
    OrganizationRiskItemResponse,
    OrganizationRiskListResponse,
    RiskAssessmentResponse,
    RiskListResponse,
    RiskScoreSummary,
)
from app.schemas.contract import (
    ContractDeleteResponse,
    ContractDetailResponse,
    ContractListResponse,
    ContractResponse,
    ContractSearchItem,
    ContractSearchRequest,
    ContractSearchResponse,
    DocumentChunkResponse,
)
from app.services.contract_analyzer import analyze_contract
from app.services.document_processor import (
    compute_file_hash,
    process_docx,
    process_pdf,
    save_upload_file,
    validate_file_format_and_size,
)
from app.services.risk_evaluator import LEGAL_DISCLAIMER, determine_risk_band

router = APIRouter()


@router.post(
    "/upload",
    response_model=ContractDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process legal contract document",
    description=(
        "Uploads a PDF or DOCX contract file (up to 15 MB), validates file signature, "
        "extracts structured text, generates chunks for vector search, and records an audit log entry."
    ),
)
async def upload_contract(
    file: UploadFile = File(..., description="PDF or DOCX contract document"),
    title: Optional[str] = Form(None, description="Optional contract title; defaults to filename"),
    description: Optional[str] = Form(None, description="Optional description of the agreement"),
    contract_type: Optional[str] = Form(ContractType.OTHER.value, description="Classification of agreement"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractDetailResponse:
    # 1. Read file bytes
    content = await file.read()

    # 2. Validate size, extension, and magic bytes
    ext = validate_file_format_and_size(file.filename or "document", content)

    # 3. Compute file hash and prepare contract identifier
    file_hash = compute_file_hash(content)
    contract_id = uuid.uuid4()
    org_id = current_user.organization_id

    # Resolve title
    doc_title = (
        title.strip()
        if title and title.strip()
        else Path(file.filename or "Contract").stem.replace("_", " ").title()
    )

    # 4. Save file to secure, randomized path inside uploads directory
    target_path, _ = save_upload_file(content, ext, org_id)

    # 5. Extract text and create document chunks
    try:
        if ext == ".pdf":
            chunks_data, extraction_meta = process_pdf(content, contract_id, org_id)
        elif ext == ".docx":
            chunks_data, extraction_meta = process_docx(content, contract_id, org_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{ext}'.",
            )
    except Exception:
        # Clean up written file from disk on processing failure
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise

    # Store file and extraction metadata in JSON
    metadata = {
        **extraction_meta,
        "original_filename": file.filename,
        "content_type": file.content_type,
    }

    # 6. Persist Contract, DocumentChunks, and AuditLog in a single transaction
    try:
        contract = Contract(
            id=contract_id,
            organization_id=org_id,
            created_by_id=current_user.id,
            title=doc_title,
            description=description.strip() if description else None,
            contract_type=contract_type if contract_type else ContractType.OTHER.value,
            status=ContractStatus.ACTIVE.value,
            file_path=str(target_path),
            file_hash=file_hash,
            file_size_bytes=len(content),
            metadata_json=metadata,
        )
        db.add(contract)

        # Bulk create document chunks
        chunk_models = [DocumentChunk(**cd) for cd in chunks_data]
        db.add_all(chunk_models)

        # Record audit log
        audit = AuditLog(
            organization_id=org_id,
            user_id=current_user.id,
            action=AuditAction.CREATE.value,
            entity_type="Contract",
            entity_id=contract_id,
            details={
                "event": "contract_upload",
                "filename": file.filename,
                "file_hash": file_hash,
                "file_size_bytes": len(content),
                "chunks_count": len(chunk_models),
            },
        )
        db.add(audit)

        db.commit()
        db.refresh(contract)
    except Exception:
        db.rollback()
        if target_path.exists():
            target_path.unlink(missing_ok=True)
        raise

    return ContractDetailResponse(
        id=contract.id,
        organization_id=contract.organization_id,
        created_by_id=contract.created_by_id,
        title=contract.title,
        description=contract.description,
        contract_type=contract.contract_type,
        status=contract.status,
        file_hash=contract.file_hash,
        file_size_bytes=contract.file_size_bytes,
        effective_date=contract.effective_date,
        expiration_date=contract.expiration_date,
        metadata_json=contract.metadata_json,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        document_chunks_count=len(chunk_models),
        document_chunks=[DocumentChunkResponse.model_validate(c) for c in chunk_models],
    )


@router.get(
    "",
    response_model=ContractListResponse,
    status_code=status.HTTP_200_OK,
    summary="List contracts for current organization",
    description="Retrieves a paginated list of contracts belonging exclusively to the authenticated user's organization.",
)
def list_contracts(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for title or description"),
    contract_type: Optional[str] = Query(None, description="Filter by contract type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by contract status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractListResponse:
    # Enforce tenant isolation strictly
    base_filter = [Contract.organization_id == current_user.organization_id]

    if search and search.strip():
        term = f"%{search.strip()}%"
        base_filter.append(
            or_(
                Contract.title.ilike(term),
                Contract.description.ilike(term),
            )
        )

    if contract_type:
        base_filter.append(Contract.contract_type == contract_type)

    if status_filter:
        base_filter.append(Contract.status == status_filter)

    # Compute total count
    count_query = select(func.count(Contract.id)).where(*base_filter)
    total = db.scalar(count_query) or 0

    # Fetch paginated items
    items_query = (
        select(Contract)
        .where(*base_filter)
        .order_by(Contract.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    contracts = db.execute(items_query).scalars().all()

    # Record audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="Contract",
        details={
            "event": "list_contracts",
            "count": len(contracts),
            "search": search,
        },
    )
    db.add(audit)
    db.commit()

    return ContractListResponse(
        items=[ContractResponse.model_validate(c) for c in contracts],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/risks",
    response_model=OrganizationRiskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List organization-wide contract risks",
    description="Retrieves a paginated list of risks identified across all contracts belonging to the authenticated organization.",
)
def list_organization_risks(
    severity: Optional[str] = Query(None, description="Filter by risk severity (critical, high, medium, low)"),
    contract_id: Optional[uuid.UUID] = Query(None, description="Filter by specific contract ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationRiskListResponse:
    # 1. Base query strictly scoped to authenticated user's organization
    base_filter = [RiskAssessment.organization_id == current_user.organization_id]

    if severity and severity.strip():
        base_filter.append(RiskAssessment.severity == severity.strip().lower())

    if contract_id:
        base_filter.append(RiskAssessment.contract_id == contract_id)

    # Total count matching filters
    total = db.scalar(select(func.count(RiskAssessment.id)).where(*base_filter)) or 0

    # Overall organization risks for scoring summary
    all_org_risks = db.execute(
        select(RiskAssessment.severity, RiskAssessment.risk_score)
        .where(*base_filter)
    ).all()

    total_score = sum(r.risk_score for r in all_org_risks)
    distribution = {
        RiskSeverity.CRITICAL.value: sum(1 for r in all_org_risks if r.severity == RiskSeverity.CRITICAL.value),
        RiskSeverity.HIGH.value: sum(1 for r in all_org_risks if r.severity == RiskSeverity.HIGH.value),
        RiskSeverity.MEDIUM.value: sum(1 for r in all_org_risks if r.severity == RiskSeverity.MEDIUM.value),
        RiskSeverity.LOW.value: sum(1 for r in all_org_risks if r.severity == RiskSeverity.LOW.value),
    }

    # Fetch paginated items joined with Contract to populate contract metadata
    query = (
        select(RiskAssessment, Contract.title, Contract.contract_type)
        .join(Contract, Contract.id == RiskAssessment.contract_id)
        .where(*base_filter)
        .order_by(RiskAssessment.risk_score.desc(), RiskAssessment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = db.execute(query).all()

    items = [
        OrganizationRiskItemResponse(
            id=risk.id,
            contract_id=risk.contract_id,
            organization_id=risk.organization_id,
            clause_id=risk.clause_id,
            title=risk.title,
            description=risk.description,
            risk_score=risk.risk_score,
            severity=risk.severity,
            category=risk.category,
            mitigation_strategy=risk.mitigation_strategy,
            status=risk.status,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
            contract_title=contract_title,
            contract_type=contract_type,
        )
        for risk, contract_title, contract_type in rows
    ]

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="RiskAssessment",
        details={
            "event": "list_organization_risks",
            "count": len(items),
            "severity": severity,
            "contract_id": str(contract_id) if contract_id else None,
        },
    )
    db.add(audit)
    db.commit()

    return OrganizationRiskListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        overall_risk_score=round(total_score, 1),
        risk_band=determine_risk_band(total_score),
        severity_distribution=distribution,
        legal_disclaimer=LEGAL_DISCLAIMER,
    )


@router.get(
    "/obligations",
    response_model=OrganizationObligationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List organization-wide contract obligations",
    description="Retrieves a paginated list of obligations and deadlines extracted across all contracts belonging to the authenticated organization.",
)
def list_organization_obligations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by obligation status"),
    contract_id: Optional[uuid.UUID] = Query(None, description="Filter by specific contract ID"),
    due_date: Optional[date] = Query(None, description="Filter by exact due date"),
    responsible_party: Optional[str] = Query(None, description="Filter by responsible party substring"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationObligationListResponse:
    # 1. Base query strictly scoped to authenticated user's organization
    base_filter = [Obligation.organization_id == current_user.organization_id]

    if status_filter:
        base_filter.append(Obligation.status == status_filter)

    if contract_id:
        base_filter.append(Obligation.contract_id == contract_id)

    if due_date:
        base_filter.append(Obligation.due_date == due_date)

    if responsible_party and responsible_party.strip():
        base_filter.append(Obligation.responsible_party.ilike(f"%{responsible_party.strip()}%"))

    # Total count matching filters
    total = db.scalar(select(func.count(Obligation.id)).where(*base_filter)) or 0

    # Fetch paginated items joined with Contract to populate contract metadata
    query = (
        select(Obligation, Contract.title, Contract.contract_type)
        .join(Contract, Contract.id == Obligation.contract_id)
        .where(*base_filter)
        .order_by(Obligation.due_date.asc().nulls_last(), Obligation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = db.execute(query).all()

    items = [
        OrganizationObligationItemResponse(
            id=ob.id,
            contract_id=ob.contract_id,
            organization_id=ob.organization_id,
            clause_id=ob.clause_id,
            title=ob.title,
            description=ob.description,
            responsible_party=ob.responsible_party,
            due_date=ob.due_date,
            frequency=ob.frequency,
            status=ob.status,
            created_at=ob.created_at,
            updated_at=ob.updated_at,
            contract_title=contract_title,
            contract_type=contract_type,
        )
        for ob, contract_title, contract_type in rows
    ]

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="Obligation",
        details={
            "event": "list_organization_obligations",
            "count": len(items),
            "status": status_filter,
            "contract_id": str(contract_id) if contract_id else None,
        },
    )
    db.add(audit)
    db.commit()

    return OrganizationObligationListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


SEARCH_DISCLAIMER = (
    "LexFlow AI deterministic search retrieves verbatim passages directly from stored "
    "document chunks. Results are not legal advice, binding conclusions, or AI-generated answers."
)

STOPWORDS = {
    "what", "is", "our", "the", "a", "an", "of", "for", "in", "to", "and", "or",
    "does", "are", "under", "upon", "have", "we", "with", "from", "by", "as",
    "at", "which", "on", "any", "all", "be", "this", "that", "there", "it",
    "can", "how", "when", "where", "who", "whom", "will", "would", "should",
}

CLAUSE_CATEGORY_KEYWORDS = {
    "Limitation of Liability": ["liability", "damages", "limitation", "indirect", "consequential", "aggregate", "cap"],
    "Termination": ["terminate", "termination", "cure", "notice to cure", "breach", "convenience", "expire", "expiration"],
    "Confidentiality": ["confidential", "proprietary", "trade secret", "non-disclosure"],
    "Indemnification": ["indemnify", "indemnification", "hold harmless", "defend", "indemnitee", "indemnitor"],
    "Payment Terms": ["payment", "invoice", "net 30", "due date", "interest", "fee", "billing", "charges"],
    "Dispute Resolution": ["dispute", "arbitration", "mediation", "venue", "court", "litigation"],
    "Governing Law": ["governing law", "jurisdiction", "construed in accordance with"],
    "Intellectual Property": ["intellectual property", "work for hire", "copyright", "patent", "trademark", "ownership"],
    "Data Protection": ["data protection", "gdpr", "personal data", "security incident", "breach notification"],
    "Renewal": ["renew", "renewal", "auto-renew", "evergreen", "term of agreement"],
    "Force Majeure": ["force majeure", "act of god", "natural disaster", "unforeseen", "pandemic"],
    "Non-Compete": ["non-compete", "non-solicitation", "restrictive covenant"],
    "Warranty": ["warranty", "warranties", "as is", "merchantability", "fitness"],
    "Delivery & Performance": ["delivery", "milestone", "acceptance", "service level", "sla"],
}

KNOWN_PARTIES = [
    "vendor", "client", "customer", "contractor", "company", "consultant",
    "service provider", "licensee", "licensor", "disclosing party", "receiving party",
    "buyer", "seller", "subcontractor", "employer", "employee",
]


@router.post(
    "/search",
    response_model=ContractSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Deterministic contract passage search",
    description="Searches actual stored document chunks for verbatim contract passages using keyword and pattern matching. Strictly isolated to the authenticated organization. Zero LLM / Zero generative AI.",
)
def search_contracts(
    payload: ContractSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractSearchResponse:
    raw_query = payload.query.strip()
    if not raw_query:
        return ContractSearchResponse(
            items=[],
            total=0,
            skip=payload.skip,
            limit=payload.limit,
            query="",
            message="No search query provided.",
            legal_disclaimer=SEARCH_DISCLAIMER,
        )

    # 1. Extract alphanumeric search keywords
    all_words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", raw_query.lower())
    keywords = [w for w in all_words if w not in STOPWORDS]
    if not keywords:
        keywords = all_words

    if not keywords:
        return ContractSearchResponse(
            items=[],
            total=0,
            skip=payload.skip,
            limit=payload.limit,
            query=raw_query,
            message="No searchable keywords found in query.",
            legal_disclaimer=SEARCH_DISCLAIMER,
        )

    # 2. Build multi-keyword SQL pattern conditions
    keyword_conditions = [DocumentChunk.content.ilike(f"%{kw}%") for kw in keywords]
    pattern_filter = or_(DocumentChunk.content.ilike(f"%{raw_query}%"), *keyword_conditions)

    base_filters = [
        DocumentChunk.organization_id == current_user.organization_id,
        pattern_filter,
    ]
    if payload.contract_id:
        base_filters.append(DocumentChunk.contract_id == payload.contract_id)

    # 3. Query SQLite for matching document chunks joined with Contract
    query = (
        select(DocumentChunk, Contract.title, Contract.contract_type)
        .join(Contract, Contract.id == DocumentChunk.contract_id)
        .where(*base_filters)
    )
    rows = db.execute(query).all()

    # 4. Rank matched chunks deterministically
    candidates = []
    for chunk, contract_title, contract_type in rows:
        content_lower = chunk.content.lower()
        exact_phrase_match = raw_query.lower() in content_lower
        matched_kws = sum(1 for kw in keywords if kw in content_lower)
        occurrences = sum(content_lower.count(kw) for kw in keywords)

        if exact_phrase_match:
            score = 0.95 + min(0.05, occurrences * 0.01)
        else:
            ratio = matched_kws / max(1, len(keywords))
            density_bonus = min(0.20, occurrences * 0.02)
            score = min(0.92, (ratio * 0.72) + density_bonus)
        score = round(max(0.10, score), 2)

        # Infer clause type from content & query
        matched_clause_type = "Contractual Passage"
        best_overlap = 0
        search_haystack = f"{raw_query.lower()} {content_lower}"
        for cat_name, cat_kws in CLAUSE_CATEGORY_KEYWORDS.items():
            overlap = sum(1 for k in cat_kws if k in search_haystack)
            if overlap > best_overlap:
                best_overlap = overlap
                matched_clause_type = cat_name

        # Infer responsible party
        responsible = "Both Parties"
        for party in KNOWN_PARTIES:
            if re.search(r"\b" + re.escape(party) + r"\b", content_lower):
                responsible = party.title()
                break

        page_info = f"Page {chunk.page_number}, Chunk #{chunk.chunk_index}" if chunk.page_number else f"Chunk #{chunk.chunk_index}"

        candidates.append({
            "item": ContractSearchItem(
                id=chunk.id,
                contract_id=chunk.contract_id,
                contract_title=contract_title,
                contract_type=contract_type,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                matched_clause_type=matched_clause_type,
                snippet=chunk.content,
                exact_match_score=score,
                responsible_party=responsible,
                source_reference=page_info,
            ),
            "score": score,
            "chunk_index": chunk.chunk_index,
        })

    # Sort deterministically by relevance score descending, then chunk index
    candidates.sort(key=lambda c: (-c["score"], c["chunk_index"]))

    total = len(candidates)
    paginated_items = [c["item"] for c in candidates[payload.skip : payload.skip + payload.limit]]

    # 5. Record structured audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="ContractSearch",
        details={
            "event": "contract_search",
            "query": raw_query,
            "contract_id": str(payload.contract_id) if payload.contract_id else None,
            "matches_found": total,
        },
    )
    db.add(audit)
    db.commit()

    return ContractSearchResponse(
        items=paginated_items,
        total=total,
        skip=payload.skip,
        limit=payload.limit,
        query=raw_query,
        message=f"Found {total} verbatim contractual match{'es' if total != 1 else ''}." if total > 0 else "No matching contract language found.",
        legal_disclaimer=SEARCH_DISCLAIMER,
    )


@router.get(
    "/{contract_id}",
    response_model=ContractDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get contract details by ID",
    description="Retrieves a specific contract and its extracted text chunks. Strictly scoped to the authenticated organization.",
)
def get_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractDetailResponse:
    # Query with strict tenant filter
    contract = db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found.",
        )

    # Retrieve chunks
    chunks = db.execute(
        select(DocumentChunk)
        .where(
            DocumentChunk.contract_id == contract.id,
            DocumentChunk.organization_id == current_user.organization_id,
        )
        .order_by(DocumentChunk.chunk_index.asc())
    ).scalars().all()

    # Record audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="Contract",
        entity_id=contract.id,
        details={"event": "view_contract_detail", "title": contract.title},
    )
    db.add(audit)
    db.commit()

    return ContractDetailResponse(
        id=contract.id,
        organization_id=contract.organization_id,
        created_by_id=contract.created_by_id,
        title=contract.title,
        description=contract.description,
        contract_type=contract.contract_type,
        status=contract.status,
        file_hash=contract.file_hash,
        file_size_bytes=contract.file_size_bytes,
        effective_date=contract.effective_date,
        expiration_date=contract.expiration_date,
        metadata_json=contract.metadata_json,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        document_chunks_count=len(chunks),
        document_chunks=[DocumentChunkResponse.model_validate(c) for c in chunks],
    )


@router.delete(
    "/{contract_id}",
    response_model=ContractDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a contract",
    description="Deletes a contract, its stored file on disk, associated document chunks, and audit logs the deletion.",
)
def delete_contract(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractDeleteResponse:
    # Query with strict tenant filter
    contract = db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found.",
        )

    # 1. Clean up file from disk safely
    if contract.file_path:
        file_path = Path(contract.file_path)
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                pass

    # 2. Record audit log before deletion
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.DELETE.value,
        entity_type="Contract",
        entity_id=contract.id,
        details={"event": "delete_contract", "title": contract.title},
    )
    db.add(audit)

    # 3. Delete from DB (cascades to document_chunks, clauses, obligations, risks)
    db.delete(contract)
    db.commit()

    return ContractDeleteResponse(
        id=contract_id,
        message="Contract and associated documents deleted successfully.",
    )


# ==============================================================================
# Milestone 5: Rule-Based Contract Analysis Endpoints
# ==============================================================================


@router.post(
    "/{contract_id}/analyze",
    response_model=ContractAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run deterministic rule-based analysis on a contract",
    description=(
        "Executes deterministic legal risk screening and obligation extraction without generative AI. "
        "Detects clauses across 14 categories, evaluates 12 risk rules, computes transparent severity scores, "
        "and extracts obligations and deadlines. Analysis results are persisted idempotently."
    ),
)
def run_contract_analysis(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractAnalysisResponse:
    return analyze_contract(db=db, contract_id=contract_id, current_user=current_user)


@router.get(
    "/{contract_id}/risks",
    response_model=RiskListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get identified risks for a contract",
    description="Retrieves identified risks and severity breakdown for a contract, strictly scoped to the authenticated organization.",
)
def get_contract_risks(
    contract_id: uuid.UUID,
    severity: Optional[str] = Query(None, description="Optional filter by severity: critical, high, medium, low"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RiskListResponse:
    # Verify contract exists for current user's organization
    contract = db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found.",
        )

    # Base query for risks
    query = select(RiskAssessment).where(
        RiskAssessment.contract_id == contract.id,
        RiskAssessment.organization_id == current_user.organization_id,
    )
    if severity:
        query = query.where(RiskAssessment.severity == severity.lower())

    risks = db.execute(query.order_by(RiskAssessment.risk_score.desc())).scalars().all()

    # Calculate overall risk score & severity distribution across all risks of this contract
    all_risks = db.execute(
        select(RiskAssessment).where(
            RiskAssessment.contract_id == contract.id,
            RiskAssessment.organization_id == current_user.organization_id,
        )
    ).scalars().all()

    total_score = sum(r.risk_score for r in all_risks)
    distribution = {
        RiskSeverity.CRITICAL.value: sum(1 for r in all_risks if r.severity == RiskSeverity.CRITICAL.value),
        RiskSeverity.HIGH.value: sum(1 for r in all_risks if r.severity == RiskSeverity.HIGH.value),
        RiskSeverity.MEDIUM.value: sum(1 for r in all_risks if r.severity == RiskSeverity.MEDIUM.value),
        RiskSeverity.LOW.value: sum(1 for r in all_risks if r.severity == RiskSeverity.LOW.value),
    }

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="Contract",
        entity_id=contract.id,
        details={"event": "view_contract_risks", "count": len(risks)},
    )
    db.add(audit)
    db.commit()

    return RiskListResponse(
        contract_id=contract.id,
        items=[RiskAssessmentResponse.model_validate(r) for r in risks],
        total=len(risks),
        total_risk_score=round(total_score, 1),
        risk_band=determine_risk_band(total_score),
        severity_distribution=distribution,
        legal_disclaimer=LEGAL_DISCLAIMER,
    )


@router.get(
    "/{contract_id}/obligations",
    response_model=ObligationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extracted obligations for a contract",
    description="Retrieves actionable contractual obligations and deadlines for a contract, strictly scoped to the authenticated organization.",
)
def get_contract_obligations(
    contract_id: uuid.UUID,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by obligation status"),
    responsible_party: Optional[str] = Query(None, description="Filter by responsible party"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ObligationListResponse:
    # Verify contract exists for current user's organization
    contract = db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found.",
        )

    query = select(Obligation).where(
        Obligation.contract_id == contract.id,
        Obligation.organization_id == current_user.organization_id,
    )

    if status_filter:
        query = query.where(Obligation.status == status_filter)
    if responsible_party:
        query = query.where(Obligation.responsible_party.ilike(f"%{responsible_party.strip()}%"))

    obligations = db.execute(query.order_by(Obligation.created_at.asc())).scalars().all()

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="Contract",
        entity_id=contract.id,
        details={"event": "view_contract_obligations", "count": len(obligations)},
    )
    db.add(audit)
    db.commit()

    return ObligationListResponse(
        contract_id=contract.id,
        items=[ObligationResponse.model_validate(o) for o in obligations],
        total=len(obligations),
    )


@router.get(
    "/{contract_id}/analysis",
    response_model=ContractAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete contract analysis summary",
    description=(
        "Retrieves the complete analysis record including all detected clauses, identified risks, "
        "obligations, and overall risk score for the contract. Strictly scoped to the authenticated organization."
    ),
)
def get_contract_analysis(
    contract_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ContractAnalysisResponse:
    # Verify contract exists for current user's organization
    contract = db.execute(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.organization_id == current_user.organization_id,
        )
    ).scalar_one_or_none()

    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found.",
        )

    # Fetch clauses, risks, obligations
    clauses = db.execute(
        select(Clause)
        .where(
            Clause.contract_id == contract.id,
            Clause.organization_id == current_user.organization_id,
        )
        .order_by(Clause.created_at.asc())
    ).scalars().all()

    risks = db.execute(
        select(RiskAssessment)
        .where(
            RiskAssessment.contract_id == contract.id,
            RiskAssessment.organization_id == current_user.organization_id,
        )
        .order_by(RiskAssessment.risk_score.desc())
    ).scalars().all()

    obligations = db.execute(
        select(Obligation)
        .where(
            Obligation.contract_id == contract.id,
            Obligation.organization_id == current_user.organization_id,
        )
        .order_by(Obligation.created_at.asc())
    ).scalars().all()

    total_score = sum(r.risk_score for r in risks)
    distribution = {
        RiskSeverity.CRITICAL.value: sum(1 for r in risks if r.severity == RiskSeverity.CRITICAL.value),
        RiskSeverity.HIGH.value: sum(1 for r in risks if r.severity == RiskSeverity.HIGH.value),
        RiskSeverity.MEDIUM.value: sum(1 for r in risks if r.severity == RiskSeverity.MEDIUM.value),
        RiskSeverity.LOW.value: sum(1 for r in risks if r.severity == RiskSeverity.LOW.value),
    }

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=AuditAction.VIEW.value,
        entity_type="Contract",
        entity_id=contract.id,
        details={"event": "view_contract_analysis", "risks_count": len(risks), "clauses_count": len(clauses)},
    )
    db.add(audit)
    db.commit()

    summary = RiskScoreSummary(
        total_risk_score=round(total_score, 1),
        risk_band=determine_risk_band(total_score),
        severity_distribution=distribution,
        total_risks_identified=len(risks),
        legal_disclaimer=LEGAL_DISCLAIMER,
    )

    return ContractAnalysisResponse(
        contract_id=contract.id,
        organization_id=contract.organization_id,
        contract_title=contract.title,
        analysis_timestamp=datetime.now(timezone.utc),
        risk_score_summary=summary,
        clauses_count=len(clauses),
        risks_count=len(risks),
        obligations_count=len(obligations),
        clauses=[ClauseResponse.model_validate(c) for c in clauses],
        risks=[RiskAssessmentResponse.model_validate(r) for r in risks],
        obligations=[ObligationResponse.model_validate(o) for o in obligations],
        legal_disclaimer=LEGAL_DISCLAIMER,
    )

