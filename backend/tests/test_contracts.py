import io
import uuid
from pathlib import Path
from typing import List, Optional
import docx
import pymupdf
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models import AuditAction, AuditLog, Contract, DocumentChunk, User, UserRole
from app.services.document_processor import process_docx, process_pdf


# ---------------------------------------------------------------------------
# Helpers to generate synthetic in-memory PDF and DOCX documents
# ---------------------------------------------------------------------------

def generate_pdf_bytes(pages_text: List[str]) -> bytes:
    """Generate a multi-page PDF with given text per page."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 72), text)
    return doc.tobytes()


def generate_empty_pdf_bytes() -> bytes:
    """Generate a PDF with a blank page (no text)."""
    doc = pymupdf.open()
    doc.new_page()
    return doc.tobytes()


def generate_docx_bytes(paragraphs: List[str], tables: Optional[List[List[List[str]]]] = None) -> bytes:
    """Generate a DOCX document with paragraphs and optional tables."""
    doc = docx.Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    if tables:
        for tbl_data in tables:
            if tbl_data:
                rows = len(tbl_data)
                cols = len(tbl_data[0])
                table = doc.add_table(rows=rows, cols=cols)
                for r_idx, row in enumerate(tbl_data):
                    for c_idx, val in enumerate(row):
                        table.cell(r_idx, c_idx).text = val
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_empty_docx_bytes() -> bytes:
    """Generate an empty DOCX document without paragraphs."""
    doc = docx.Document()
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers_org_a(client):
    """Register and authenticate user for Organization A."""
    email = f"user_a_{uuid.uuid4().hex[:6]}@orga.com"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Counsel A",
        "email": email,
        "password": "Password123!",
        "organization_name": f"Org A {uuid.uuid4().hex[:4]}",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_org_b(client):
    """Register and authenticate user for Organization B."""
    email = f"user_b_{uuid.uuid4().hex[:6]}@orgb.com"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Counsel B",
        "email": email,
        "password": "Password123!",
        "organization_name": f"Org B {uuid.uuid4().hex[:4]}",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_upload_valid_pdf(client, auth_headers_org_a, tmp_path, monkeypatch):
    """
    Test uploading a valid multi-page PDF contract.
    Verifies 201 Created, metadata population, chunks creation, and no file_path leakage.
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    pdf_content = generate_pdf_bytes([
        "Page 1: Master Services Agreement by and between Party A and Party B.",
        "Page 2: Confidentiality and non-disclosure obligations shall survive for 5 years.",
    ])

    files = {"file": ("test_agreement.pdf", pdf_content, "application/pdf")}
    data = {
        "title": "Master Services Agreement 2026",
        "description": "Enterprise cloud services agreement",
        "contract_type": "msa",
    }

    response = client.post("/api/v1/contracts/upload", files=files, data=data, headers=auth_headers_org_a)
    assert response.status_code == 201

    res_json = response.json()
    assert res_json["title"] == "Master Services Agreement 2026"
    assert res_json["description"] == "Enterprise cloud services agreement"
    assert res_json["contract_type"] == "msa"
    assert res_json["status"] == "active"
    assert res_json["file_size_bytes"] == len(pdf_content)
    assert res_json["file_hash"] is not None
    # Crucial security assertion: internal filesystem path is NEVER exposed
    assert "file_path" not in res_json

    # Document chunks assertion
    assert res_json["document_chunks_count"] >= 2
    chunks = res_json["document_chunks"]
    assert chunks[0]["page_number"] == 1
    assert "Master Services Agreement" in chunks[0]["content"]
    assert chunks[1]["page_number"] == 2
    assert "Confidentiality" in chunks[1]["content"]


def test_upload_valid_docx(client, auth_headers_org_a, tmp_path, monkeypatch):
    """
    Test uploading a valid DOCX contract.
    Verifies 201 Created, chunks creation, page_number is strictly None for DOCX.
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    docx_content = generate_docx_bytes(
        paragraphs=[
            "Non-Disclosure Agreement preamble.",
            "Section 1: Definition of Confidential Information.",
            "Section 2: Permitted disclosures and standard exclusions.",
        ],
        tables=[
            [["Deliverable", "Timeline"], ["Initial Report", "30 Days"], ["Final Audit", "90 Days"]]
        ],
    )

    files = {"file": ("nda_contract.docx", docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    data = {"contract_type": "nda"}

    response = client.post("/api/v1/contracts/upload", files=files, data=data, headers=auth_headers_org_a)
    assert response.status_code == 201

    res_json = response.json()
    assert res_json["title"] == "Nda Contract"  # Auto-generated title from filename
    assert res_json["document_chunks_count"] >= 1

    chunks = res_json["document_chunks"]
    for c in chunks:
        # Crucial requirement: Do not invent page numbers for DOCX
        assert c["page_number"] is None
        assert c["embedding_metadata"]["source_type"] == "docx"


def test_upload_invalid_file_extension(client, auth_headers_org_a):
    """
    Test rejecting files with invalid extensions (.txt, .exe, .png).
    """
    files = {"file": ("contract.txt", b"Plain text file content", "text/plain")}
    response = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    assert response.status_code == 400
    assert "unsupported file format" in response.json()["detail"].lower()


def test_upload_spoofed_file_format(client, auth_headers_org_a):
    """
    Test rejecting files where extension is .pdf or .docx but magic bytes are invalid.
    """
    # Text file disguised as PDF
    fake_pdf = b"This is just a text file renamed to .pdf"
    files = {"file": ("malicious.pdf", fake_pdf, "application/pdf")}
    res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    assert res.status_code == 400
    assert "invalid pdf" in res.json()["detail"].lower()

    # Plain zip or text file disguised as DOCX
    fake_docx = b"Not a real word docx document"
    files = {"file": ("fake.docx", fake_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    assert res.status_code == 400
    assert "invalid docx" in res.json()["detail"].lower()


def test_upload_empty_file(client, auth_headers_org_a):
    """
    Test rejecting a 0-byte file.
    """
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_upload_unreadable_or_scanned_pdf(client, auth_headers_org_a):
    """
    Test detecting empty or scanned PDFs without extractable text.
    """
    empty_pdf = generate_empty_pdf_bytes()
    files = {"file": ("scanned_blank.pdf", empty_pdf, "application/pdf")}
    res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    assert res.status_code == 400
    assert "no extractable text" in res.json()["detail"].lower()


def test_upload_oversized_file(client, auth_headers_org_a, monkeypatch):
    """
    Test that uploads exceeding MAX_UPLOAD_SIZE_BYTES are rejected.
    """
    # Temporarily set max upload size to 100 KB for test speed
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 100 * 1024)

    oversized_data = b"%PDF-1.4 " + b"0" * (120 * 1024)
    files = {"file": ("large.pdf", oversized_data, "application/pdf")}
    res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    assert res.status_code == 413
    assert "exceeds" in res.json()["detail"].lower()


def test_text_extraction_and_chunking():
    """
    Direct unit test for process_pdf and process_docx chunking and sequential indexing.
    """
    dummy_contract_id = uuid.uuid4()
    dummy_org_id = uuid.uuid4()

    # 1. Test PDF extraction
    pdf_bytes = generate_pdf_bytes(["Paragraph 1 content.", "Paragraph 2 content."])
    pdf_chunks, pdf_meta = process_pdf(pdf_bytes, dummy_contract_id, dummy_org_id)
    assert len(pdf_chunks) == 2
    assert pdf_chunks[0]["chunk_index"] == 0
    assert pdf_chunks[1]["chunk_index"] == 1
    assert pdf_chunks[0]["page_number"] == 1
    assert pdf_chunks[1]["page_number"] == 2
    assert pdf_meta["page_count"] == 2

    # 2. Test DOCX extraction
    docx_bytes = generate_docx_bytes(["Clause 1 text", "Clause 2 text"])
    docx_chunks, docx_meta = process_docx(docx_bytes, dummy_contract_id, dummy_org_id)
    assert len(docx_chunks) >= 1
    assert docx_chunks[0]["page_number"] is None
    assert docx_meta["paragraph_count"] == 2


def test_contract_listing_and_pagination(client, auth_headers_org_a, tmp_path, monkeypatch):
    """
    Test GET /api/v1/contracts with pagination and search filtering.
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    # Upload 3 distinct contracts
    for i in range(3):
        pdf = generate_pdf_bytes([f"Page text for contract {i}"])
        files = {"file": (f"contract_{i}.pdf", pdf, "application/pdf")}
        data = {"title": f"Agreement Number {i}", "contract_type": "vendor"}
        client.post("/api/v1/contracts/upload", files=files, data=data, headers=auth_headers_org_a)

    # Test limit=2
    res = client.get("/api/v1/contracts?skip=0&limit=2", headers=auth_headers_org_a)
    assert res.status_code == 200
    res_data = res.json()
    assert len(res_data["items"]) == 2
    assert res_data["total"] >= 3

    # Test search query
    search_res = client.get("/api/v1/contracts?search=Number 1", headers=auth_headers_org_a)
    assert search_res.status_code == 200
    search_items = search_res.json()["items"]
    assert len(search_items) == 1
    assert search_items[0]["title"] == "Agreement Number 1"


def test_contract_retrieval_by_id(client, auth_headers_org_a, tmp_path, monkeypatch):
    """
    Test GET /api/v1/contracts/{contract_id} returns full details with chunks.
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    pdf = generate_pdf_bytes(["Single page agreement text."])
    files = {"file": ("retrieve_test.pdf", pdf, "application/pdf")}
    up_res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    contract_id = up_res.json()["id"]

    res = client.get(f"/api/v1/contracts/{contract_id}", headers=auth_headers_org_a)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == contract_id
    assert data["document_chunks_count"] >= 1
    assert len(data["document_chunks"]) >= 1


def test_contract_deletion_and_file_cleanup(client, auth_headers_org_a, db_session, tmp_path, monkeypatch):
    """
    Test DELETE /api/v1/contracts/{contract_id}:
    - Removes record from database.
    - Cascades deletion of document chunks.
    - Removes stored file from disk.
    """
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))

    pdf = generate_pdf_bytes(["Text to be deleted."])
    files = {"file": ("to_delete.pdf", pdf, "application/pdf")}
    up_res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    contract_id = uuid.UUID(up_res.json()["id"])

    # Locate saved file on disk via DB
    db_contract = db_session.execute(select(Contract).filter_by(id=contract_id)).scalar_one()
    file_path = Path(db_contract.file_path)
    assert file_path.exists() is True

    # Delete contract
    del_res = client.delete(f"/api/v1/contracts/{contract_id}", headers=auth_headers_org_a)
    assert del_res.status_code == 200
    assert del_res.json()["id"] == str(contract_id)

    # Verify database deletion
    deleted_contract = db_session.execute(select(Contract).filter_by(id=contract_id)).scalar_one_or_none()
    assert deleted_contract is None

    # Verify cascaded chunks deletion
    chunks = db_session.execute(select(DocumentChunk).filter_by(contract_id=contract_id)).scalars().all()
    assert len(chunks) == 0

    # Verify physical file deletion from disk
    assert file_path.exists() is False


def test_unauthorized_access(client):
    """
    Test that unauthenticated requests to contracts endpoints are rejected with 401.
    """
    # Upload
    files = {"file": ("unauth.pdf", b"%PDF-1.4 test", "application/pdf")}
    assert client.post("/api/v1/contracts/upload", files=files).status_code == 401

    # List
    assert client.get("/api/v1/contracts").status_code == 401

    # Get
    fake_id = uuid.uuid4()
    assert client.get(f"/api/v1/contracts/{fake_id}").status_code == 401

    # Delete
    assert client.delete(f"/api/v1/contracts/{fake_id}").status_code == 401


def test_cross_organization_access_prevention(client, auth_headers_org_a, auth_headers_org_b, tmp_path, monkeypatch):
    """
    Verify strict tenant isolation:
    - User in Org B cannot see Org A's contracts in list.
    - User in Org B cannot retrieve Org A's contract by ID (returns 404).
    - User in Org B cannot delete Org A's contract (returns 404).
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    # Org A uploads a contract
    pdf = generate_pdf_bytes(["Confidential Org A contract."])
    files = {"file": ("org_a_contract.pdf", pdf, "application/pdf")}
    up_res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    org_a_contract_id = up_res.json()["id"]

    # 1. Org B lists contracts -> should not include Org A's contract
    list_b = client.get("/api/v1/contracts", headers=auth_headers_org_b)
    assert list_b.status_code == 200
    ids_in_b = [item["id"] for item in list_b.json()["items"]]
    assert org_a_contract_id not in ids_in_b

    # 2. Org B attempts to retrieve Org A's contract -> 404 Not Found
    get_b = client.get(f"/api/v1/contracts/{org_a_contract_id}", headers=auth_headers_org_b)
    assert get_b.status_code == 404

    # 3. Org B attempts to delete Org A's contract -> 404 Not Found
    del_b = client.delete(f"/api/v1/contracts/{org_a_contract_id}", headers=auth_headers_org_b)
    assert del_b.status_code == 404


def test_audit_logging_for_contracts(client, auth_headers_org_a, db_session, tmp_path, monkeypatch):
    """
    Verify that upload, viewing, and deletion create audit logs associated with the user and org.
    """
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

    pdf = generate_pdf_bytes(["Audit log verification document."])
    files = {"file": ("audit_contract.pdf", pdf, "application/pdf")}
    up_res = client.post("/api/v1/contracts/upload", files=files, headers=auth_headers_org_a)
    contract_id = uuid.UUID(up_res.json()["id"])

    # View contract
    client.get(f"/api/v1/contracts/{contract_id}", headers=auth_headers_org_a)

    # Delete contract
    client.delete(f"/api/v1/contracts/{contract_id}", headers=auth_headers_org_a)

    # Query audit logs for this contract
    audits = db_session.execute(
        select(AuditLog)
        .where(AuditLog.entity_id == contract_id)
        .order_by(AuditLog.created_at.asc())
    ).scalars().all()

    actions = [a.action for a in audits]
    assert AuditAction.CREATE.value in actions  # Upload
    assert AuditAction.VIEW.value in actions    # View
    assert AuditAction.DELETE.value in actions  # Delete
