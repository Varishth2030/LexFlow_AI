"""
LexFlow AI - Contract Analysis Orchestration Service.

Coordinates deterministic clause detection, risk evaluation & scoring,
and obligation extraction. Ensures idempotent persistence, strict tenant isolation,
and audit logging.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import AuditAction, AuditLog, Clause, Contract, DocumentChunk, Obligation, RiskAssessment, User
from app.schemas.analysis import (
    ClauseResponse,
    ContractAnalysisResponse,
    ObligationResponse,
    RiskAssessmentResponse,
    RiskScoreSummary,
)
from app.services.clause_detector import DetectedClause, detect_clauses_in_chunks
from app.services.obligation_extractor import ExtractedObligation, extract_obligations_from_clauses
from app.services.risk_evaluator import LEGAL_DISCLAIMER, RiskScoringResult, evaluate_contract_risks


def analyze_contract(
    db: Session,
    contract_id: uuid.UUID,
    current_user: User,
) -> ContractAnalysisResponse:
    """
    Executes complete deterministic rule-based analysis for a contract:
    1. Validates organization-level tenant access.
    2. Retrieves document chunks.
    3. Detects clauses across 14 categories.
    4. Evaluates risks against 12-rule catalogue and computes score & band.
    5. Extracts actionable obligations, responsible parties, and deadlines.
    6. Persists results idempotently within a transaction.
    7. Records audit log entry.
    """
    # 1. Tenant-scoped contract retrieval
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

    # 2. Fetch document chunks
    chunks = db.execute(
        select(DocumentChunk)
        .where(
            DocumentChunk.contract_id == contract.id,
            DocumentChunk.organization_id == current_user.organization_id,
        )
        .order_by(DocumentChunk.chunk_index.asc())
    ).scalars().all()

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract has no extracted text chunks to analyze. Please re-upload or process the file first.",
        )

    # 3. Detect clauses
    detected_clauses: List[DetectedClause] = detect_clauses_in_chunks(chunks)

    # 4. Evaluate risks and score
    risk_result: RiskScoringResult = evaluate_contract_risks(detected_clauses, chunks)

    # 5. Extract obligations
    extracted_obligations: List[ExtractedObligation] = extract_obligations_from_clauses(detected_clauses, chunks)

    org_id = current_user.organization_id

    # 6. Idempotent persistence inside a transaction
    try:
        # A. Remove any previous analysis records for this contract to guarantee idempotency
        db.execute(
            delete(RiskAssessment).where(
                RiskAssessment.contract_id == contract.id,
                RiskAssessment.organization_id == org_id,
            )
        )
        db.execute(
            delete(Obligation).where(
                Obligation.contract_id == contract.id,
                Obligation.organization_id == org_id,
            )
        )
        db.execute(
            delete(Clause).where(
                Clause.contract_id == contract.id,
                Clause.organization_id == org_id,
            )
        )
        db.flush()

        # B. Persist clauses and map indices
        clause_id_map: dict[int, uuid.UUID] = {}
        persisted_clauses: List[Clause] = []

        for idx, dc in enumerate(detected_clauses):
            c_id = uuid.uuid4()
            clause_model = Clause(
                id=c_id,
                contract_id=contract.id,
                organization_id=org_id,
                clause_type=dc.clause_type,
                title=dc.title,
                text=dc.text,
                page_number=dc.page_number,
                risk_level=dc.risk_level,
            )
            persisted_clauses.append(clause_model)
            clause_id_map[idx] = c_id

        if persisted_clauses:
            db.add_all(persisted_clauses)
            db.flush()

        # C. Persist risk assessments
        persisted_risks: List[RiskAssessment] = []
        for r in risk_result.risks:
            clause_fk = clause_id_map.get(r.clause_index) if r.clause_index is not None else None
            risk_model = RiskAssessment(
                id=uuid.uuid4(),
                contract_id=contract.id,
                organization_id=org_id,
                clause_id=clause_fk,
                title=r.title,
                description=r.description,
                risk_score=r.risk_score,
                severity=r.severity,
                category=r.category,
                mitigation_strategy=r.mitigation_strategy,
                status=r.status,
            )
            persisted_risks.append(risk_model)

        if persisted_risks:
            db.add_all(persisted_risks)

        # D. Persist obligations
        persisted_obligations: List[Obligation] = []
        for ob in extracted_obligations:
            clause_fk = clause_id_map.get(ob.clause_index) if ob.clause_index is not None else None
            obligation_model = Obligation(
                id=uuid.uuid4(),
                contract_id=contract.id,
                organization_id=org_id,
                clause_id=clause_fk,
                title=ob.title,
                description=ob.description,
                responsible_party=ob.responsible_party,
                due_date=ob.due_date,
                frequency=ob.frequency,
                status=ob.status,
            )
            persisted_obligations.append(obligation_model)

        if persisted_obligations:
            db.add_all(persisted_obligations)

        # E. Audit logging
        audit = AuditLog(
            organization_id=org_id,
            user_id=current_user.id,
            action=AuditAction.CREATE.value,
            entity_type="Contract",
            entity_id=contract.id,
            details={
                "event": "contract_analysis",
                "total_risk_score": risk_result.total_risk_score,
                "risk_band": risk_result.risk_band,
                "clauses_detected": len(persisted_clauses),
                "risks_identified": len(persisted_risks),
                "obligations_extracted": len(persisted_obligations),
            },
        )
        db.add(audit)

        db.commit()

        # Refresh instances for response serialization
        for c in persisted_clauses:
            db.refresh(c)
        for r in persisted_risks:
            db.refresh(r)
        for o in persisted_obligations:
            db.refresh(o)

    except Exception:
        db.rollback()
        raise

    summary = RiskScoreSummary(
        total_risk_score=risk_result.total_risk_score,
        risk_band=risk_result.risk_band,
        severity_distribution=risk_result.severity_distribution,
        total_risks_identified=risk_result.total_risks_identified,
        legal_disclaimer=LEGAL_DISCLAIMER,
    )

    return ContractAnalysisResponse(
        contract_id=contract.id,
        organization_id=contract.organization_id,
        contract_title=contract.title,
        analysis_timestamp=datetime.now(timezone.utc),
        risk_score_summary=summary,
        clauses_count=len(persisted_clauses),
        risks_count=len(persisted_risks),
        obligations_count=len(persisted_obligations),
        clauses=[ClauseResponse.model_validate(c) for c in persisted_clauses],
        risks=[RiskAssessmentResponse.model_validate(r) for r in persisted_risks],
        obligations=[ObligationResponse.model_validate(o) for o in persisted_obligations],
        legal_disclaimer=LEGAL_DISCLAIMER,
    )
