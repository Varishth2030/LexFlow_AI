"""
LexFlow AI - Test Suite for Milestone 8A: Organization-Wide Risks and Obligations APIs.
"""

import io
import fitz
import pytest


def generate_pdf_bytes(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((50, 72), text, fontsize=11)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


@pytest.fixture(scope="function")
def auth_headers_org_a(client):
    reg_data = {
        "full_name": "Counsel Alpha",
        "email": "alpha@firm-a.com",
        "password": "Password123!",
        "organization_name": "Organization Alpha",
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_org_b(client):
    reg_data = {
        "full_name": "Counsel Beta",
        "email": "beta@firm-b.com",
        "password": "Password123!",
        "organization_name": "Organization Beta",
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestOrganizationRisksAPI:
    """Tests for GET /api/v1/contracts/risks."""

    def test_organization_risks_empty(self, client, auth_headers_org_a):
        res = client.get("/api/v1/contracts/risks", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["overall_risk_score"] == 0.0
        assert data["risk_band"] == "Low"
        assert "legal_disclaimer" in data

    def test_organization_risks_retrieval_and_metadata(self, client, auth_headers_org_a):
        # 1. Upload Contract 1 with unlimited liability
        text1 = (
            "MASTER SERVICES AGREEMENT\n\n"
            "Section 1. Payment Terms. Invoices shall be paid within 30 days.\n\n"
            "Section 2. Limitation of Liability. Vendor liability shall be without limitation for breaches.\n"
        )
        pdf1 = generate_pdf_bytes([text1])
        c1_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c1.pdf", pdf1, "application/pdf")},
            data={"title": "Master Services Agreement 1", "contract_type": "msa"},
        )
        assert c1_res.status_code == 201
        c1_id = c1_res.json()["id"]

        # Analyze Contract 1
        a1 = client.post(f"/api/v1/contracts/{c1_id}/analyze", headers=auth_headers_org_a)
        assert a1.status_code == 200

        # 2. Upload Contract 2 with unilateral termination
        text2 = (
            "VENDOR AGREEMENT\n\n"
            "Section 1. Termination. Customer may terminate at its sole discretion without cause.\n"
        )
        pdf2 = generate_pdf_bytes([text2])
        c2_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c2.pdf", pdf2, "application/pdf")},
            data={"title": "Vendor IT Agreement", "contract_type": "vendor"},
        )
        assert c2_res.status_code == 201
        c2_id = c2_res.json()["id"]

        # Analyze Contract 2
        a2 = client.post(f"/api/v1/contracts/{c2_id}/analyze", headers=auth_headers_org_a)
        assert a2.status_code == 200

        # 3. Query organization-wide risks
        res = client.get("/api/v1/contracts/risks", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
        assert data["overall_risk_score"] > 0

        # Verify contract title and type are included
        contract_titles = [item["contract_title"] for item in data["items"]]
        assert "Master Services Agreement 1" in contract_titles
        assert "Vendor IT Agreement" in contract_titles

    def test_organization_risks_severity_filtering(self, client, auth_headers_org_a):
        text = (
            "AGREEMENT\n\n"
            "Section 1. Limitation. Vendor liability shall be without limitation.\n"
        )
        pdf = generate_pdf_bytes([text])
        c = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c.pdf", pdf, "application/pdf")},
            data={"title": "Risk Filter Contract"},
        )
        cid = c.json()["id"]
        client.post(f"/api/v1/contracts/{cid}/analyze", headers=auth_headers_org_a)

        # Filter by critical
        res = client.get("/api/v1/contracts/risks?severity=critical", headers=auth_headers_org_a)
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["severity"] == "critical"

    def test_organization_risks_contract_filtering(self, client, auth_headers_org_a):
        text = "AGREEMENT\n\nSection 1. Payment net 30.\n"
        pdf = generate_pdf_bytes([text])
        c = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c.pdf", pdf, "application/pdf")},
            data={"title": "Target Contract"},
        )
        cid = c.json()["id"]
        client.post(f"/api/v1/contracts/{cid}/analyze", headers=auth_headers_org_a)

        res = client.get(f"/api/v1/contracts/risks?contract_id={cid}", headers=auth_headers_org_a)
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["contract_id"] == cid

    def test_organization_risks_pagination(self, client, auth_headers_org_a):
        res = client.get("/api/v1/contracts/risks?skip=0&limit=1", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["skip"] == 0
        assert data["limit"] == 1
        assert len(data["items"]) <= 1

    def test_organization_risks_tenant_isolation(self, client, auth_headers_org_a, auth_headers_org_b):
        # Upload & analyze in Org A
        text = "AGREEMENT\n\nSection 1. Liability without limitation.\n"
        pdf = generate_pdf_bytes([text])
        c = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c.pdf", pdf, "application/pdf")},
            data={"title": "Org A Contract"},
        )
        cid = c.json()["id"]
        client.post(f"/api/v1/contracts/{cid}/analyze", headers=auth_headers_org_a)

        # Org B queries risks
        res_b = client.get("/api/v1/contracts/risks", headers=auth_headers_org_b)
        assert res_b.status_code == 200
        assert res_b.json()["total"] == 0
        assert res_b.json()["items"] == []


class TestOrganizationObligationsAPI:
    """Tests for GET /api/v1/contracts/obligations."""

    def test_organization_obligations_empty(self, client, auth_headers_org_a):
        res = client.get("/api/v1/contracts/obligations", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_organization_obligations_retrieval_and_metadata(self, client, auth_headers_org_a):
        text = (
            "MASTER SERVICES AGREEMENT\n\n"
            "Section 1. Payment Terms. Customer shall remit payment within 30 days of invoice.\n\n"
            "Section 2. Compliance. Vendor shall provide quarterly audit reports.\n"
        )
        pdf = generate_pdf_bytes([text])
        c_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("contract.pdf", pdf, "application/pdf")},
            data={"title": "Global Obligation Agreement", "contract_type": "msa"},
        )
        cid = c_res.json()["id"]
        client.post(f"/api/v1/contracts/{cid}/analyze", headers=auth_headers_org_a)

        res = client.get("/api/v1/contracts/obligations", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        first_item = data["items"][0]
        assert first_item["contract_title"] == "Global Obligation Agreement"
        assert first_item["contract_type"] == "msa"
        assert "responsible_party" in first_item

    def test_organization_obligations_status_filter(self, client, auth_headers_org_a):
        res = client.get("/api/v1/contracts/obligations?status=pending", headers=auth_headers_org_a)
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["status"] == "pending"

    def test_organization_obligations_tenant_isolation(self, client, auth_headers_org_a, auth_headers_org_b):
        text = "AGREEMENT\n\nSection 1. Client shall pay within 30 days.\n"
        pdf = generate_pdf_bytes([text])
        c = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c.pdf", pdf, "application/pdf")},
            data={"title": "Org A Agreement"},
        )
        cid = c.json()["id"]
        client.post(f"/api/v1/contracts/{cid}/analyze", headers=auth_headers_org_a)

        # Org B should see 0 obligations
        res_b = client.get("/api/v1/contracts/obligations", headers=auth_headers_org_b)
        assert res_b.status_code == 200
        assert res_b.json()["total"] == 0
        assert res_b.json()["items"] == []


class TestContractListCompatibility:
    """Verifies contract listing response structure."""

    def test_contract_list_contains_items_and_contracts(self, client, auth_headers_org_a):
        text = "AGREEMENT\n\nSimple text content.\n"
        pdf = generate_pdf_bytes([text])
        client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c.pdf", pdf, "application/pdf")},
            data={"title": "Compatibility Test Agreement"},
        )

        res = client.get("/api/v1/contracts", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "contracts" in data
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert len(data["items"]) >= 1
        assert len(data["contracts"]) == len(data["items"])


class TestUnauthorizedAccess:
    """Verifies that endpoints reject unauthenticated requests."""

    def test_risks_requires_auth(self, client):
        res = client.get("/api/v1/contracts/risks")
        assert res.status_code == 401

    def test_obligations_requires_auth(self, client):
        res = client.get("/api/v1/contracts/obligations")
        assert res.status_code == 401
