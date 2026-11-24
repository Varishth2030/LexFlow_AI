"""
LexFlow AI - Test Suite for Milestone 9: Executive Reports & Export Engine.
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
        "full_name": "General Counsel A",
        "email": "gc_a@firm-a.com",
        "password": "Password123!",
        "organization_name": "Acme Legal Corp",
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_org_b(client):
    reg_data = {
        "full_name": "General Counsel B",
        "email": "gc_b@firm-b.com",
        "password": "Password123!",
        "organization_name": "Beta Legal Corp",
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestExecutiveReportsAPI:
    """Tests for /api/v1/reports endpoints."""

    def test_report_summary_empty(self, client, auth_headers_org_a):
        res = client.get("/api/v1/reports/summary", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total_contracts"] == 0
        assert data["total_clauses"] == 0
        assert data["total_risks"] == 0
        assert data["organization_name"] == "Acme Legal Corp"
        assert "legal_disclaimer" in data
        assert len(data["risk_trend"]) == 5

    def test_report_summary_populated(self, client, auth_headers_org_a):
        # 1. Upload contract with critical liability and payment terms
        contract_text = (
            "MASTER SERVICES AGREEMENT\n\n"
            "Section 1. Payment Terms. Invoices shall be paid within thirty (30) days.\n\n"
            "Section 2. Limitation of Liability. Vendor liability shall be without limitation for all damages.\n"
        )
        pdf = generate_pdf_bytes([contract_text])
        up_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("report_msa.pdf", pdf, "application/pdf")},
            data={"title": "Enterprise Cloud MSA", "contract_type": "msa"},
        )
        assert up_res.status_code == 201
        contract_id = up_res.json()["id"]

        # 2. Analyze contract
        client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=auth_headers_org_a)

        # 3. Create compliance control and task
        ctrl_res = client.post(
            "/api/v1/compliance/controls",
            headers=auth_headers_org_a,
            json={
                "name": "Vendor Risk Review",
                "description": "Annual vendor risk and liability assessment.",
                "category": "Risk Management",
                "framework": "soc2",
                "requirement": "Annual review of vendor risk posture.",
            },
        )
        assert ctrl_res.status_code == 201, ctrl_res.text
        ctrl = ctrl_res.json()

        client.post(
            "/api/v1/compliance/tasks",
            headers=auth_headers_org_a,
            json={
                "title": "Review Cloud MSA Liability",
                "control_id": ctrl["id"],
                "priority": "critical",
                "status": "completed",
            },
        )

        # 4. Fetch summary
        res = client.get("/api/v1/reports/summary", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total_contracts"] == 1
        assert data["total_clauses"] >= 1
        assert data["total_risks"] >= 1
        assert data["critical_risks"] >= 1
        assert data["total_controls"] == 1
        assert data["active_controls"] == 1
        assert data["total_compliance_tasks"] == 1
        assert data["completed_compliance_tasks"] == 1
        assert data["compliance_governance_rate"] == 100.0

        # Verify contract type distribution
        types = {t["name"]: t["count"] for t in data["contract_type_distribution"]}
        assert "Master Services (MSA)" in types
        assert types["Master Services (MSA)"] == 1

    def test_report_summary_tenant_isolation(self, client, auth_headers_org_a, auth_headers_org_b):
        # Org A uploads contract
        pdf_a = generate_pdf_bytes(["CONFIDENTIAL AGREEMENT A"])
        client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("contract_a.pdf", pdf_a, "application/pdf")},
            data={"title": "Org A Contract", "contract_type": "msa"},
        )

        # Org B queries summary
        res_b = client.get("/api/v1/reports/summary", headers=auth_headers_org_b)
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["total_contracts"] == 0
        assert data_b["organization_name"] == "Beta Legal Corp"

    def test_export_csv_executive(self, client, auth_headers_org_a):
        res = client.get("/api/v1/reports/export/csv?type=executive", headers=auth_headers_org_a)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert "attachment" in res.headers["content-disposition"]
        content = res.text
        assert "LEXFLOW AI" in content
        assert "CONTRACT INVENTORY" in content
        assert "LEGAL RISK REGISTER" in content

    def test_export_csv_risks_and_obligations(self, client, auth_headers_org_a):
        # Test risks CSV
        res_risks = client.get("/api/v1/reports/export/csv?type=risks", headers=auth_headers_org_a)
        assert res_risks.status_code == 200
        assert "Risk ID,Contract Title,Contract Type,Category" in res_risks.text

        # Test obligations CSV
        res_ob = client.get("/api/v1/reports/export/csv?type=obligations", headers=auth_headers_org_a)
        assert res_ob.status_code == 200
        assert "Obligation ID,Contract Title,Title,Responsible Party" in res_ob.text

    def test_export_pdf_report(self, client, auth_headers_org_a):
        res = client.get("/api/v1/reports/export/pdf", headers=auth_headers_org_a)
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert "attachment" in res.headers["content-disposition"]
        # PDF magic bytes
        assert res.content.startswith(b"%PDF-")
        assert len(res.content) > 1000

    def test_reports_unauthenticated(self, client):
        assert client.get("/api/v1/reports/summary").status_code == 401
        assert client.get("/api/v1/reports/export/csv").status_code == 401
        assert client.get("/api/v1/reports/export/pdf").status_code == 401

    def test_reports_audit_logging(self, client, auth_headers_org_a):
        # Trigger export
        client.get("/api/v1/reports/export/pdf", headers=auth_headers_org_a)

        # Verify audit record
        audit_res = client.get("/api/v1/audit?action=export", headers=auth_headers_org_a)
        assert audit_res.status_code == 200
        data = audit_res.json()
        assert data["total"] >= 1
        actions = [log["action"].lower() for log in data["items"]]
        assert "export" in actions
