"""
LexFlow AI - Test Suite for Milestone 8B: Live Contract Search and Audit Logs.
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
        "email": "alpha_search@firm-a.com",
        "password": "Password123!",
        "organization_name": "Organization Search Alpha",
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_org_b(client):
    reg_data = {
        "full_name": "Counsel Beta",
        "email": "beta_search@firm-b.com",
        "password": "Password123!",
        "organization_name": "Organization Search Beta",
    }
    res = client.post("/api/v1/auth/register", json=reg_data)
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestContractSearchAPI:
    """Tests for POST /api/v1/contracts/search."""

    def test_search_empty_query(self, client, auth_headers_org_a):
        res = client.post(
            "/api/v1/contracts/search",
            headers=auth_headers_org_a,
            json={"query": "   "},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert "No search query provided" in data["message"]
        assert "legal_disclaimer" in data

    def test_search_no_results(self, client, auth_headers_org_a):
        # Upload a standard contract
        text = "GENERAL SERVICES AGREEMENT\n\nSection 1. Standard provisions and terms."
        pdf = generate_pdf_bytes([text])
        up_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("contract.pdf", pdf, "application/pdf")},
            data={"title": "General Agreement", "contract_type": "service"},
        )
        assert up_res.status_code == 201

        # Search for non-existent terms
        res = client.post(
            "/api/v1/contracts/search",
            headers=auth_headers_org_a,
            json={"query": "quantum teleportation orbital mechanics"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert "No matching contract language found" in data["message"]

    def test_search_exact_source_passage_retrieval(self, client, auth_headers_org_a):
        verbatim_passage = (
            "MASTER SERVICES AGREEMENT\n\n"
            "Section 7. Limitation of Liability.\n"
            "The aggregate liability of Vendor under this Agreement shall not exceed fifty thousand dollars ($50,000).\n"
            "Neither party shall be liable for indirect or consequential damages."
        )
        pdf = generate_pdf_bytes([verbatim_passage])
        up_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("msa_search.pdf", pdf, "application/pdf")},
            data={"title": "Acme MSA Contract", "contract_type": "msa"},
        )
        assert up_res.status_code == 201
        contract_id = up_res.json()["id"]

        # Search for liability cap
        res = client.post(
            "/api/v1/contracts/search",
            headers=auth_headers_org_a,
            json={"query": "What is our aggregate limitation of liability cap?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        top_match = data["items"][0]
        assert top_match["contract_id"] == contract_id
        assert top_match["contract_title"] == "Acme MSA Contract"
        assert top_match["contract_type"] == "msa"
        assert "Limitation of Liability" in top_match["matched_clause_type"]
        assert "fifty thousand dollars" in top_match["snippet"]
        assert top_match["exact_match_score"] > 0.0
        assert top_match["chunk_index"] == 0
        assert top_match["page_number"] == 1
        assert "Page 1, Chunk #0" in top_match["source_reference"]

    def test_search_contract_id_filtering(self, client, auth_headers_org_a):
        # Contract 1: Indemnification terms
        text1 = "CONTRACT ALPHA\n\nSection 1. Indemnification. Vendor covenants to defend and hold harmless Client."
        pdf1 = generate_pdf_bytes([text1])
        c1 = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c1.pdf", pdf1, "application/pdf")},
            data={"title": "Contract Alpha", "contract_type": "vendor"},
        ).json()

        # Contract 2: Another indemnification contract
        text2 = "CONTRACT BETA\n\nSection 1. Indemnification. Contractor covenants to defend and hold harmless Company."
        pdf2 = generate_pdf_bytes([text2])
        c2 = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("c2.pdf", pdf2, "application/pdf")},
            data={"title": "Contract Beta", "contract_type": "vendor"},
        ).json()

        # Search targeting only Contract Alpha
        res = client.post(
            "/api/v1/contracts/search",
            headers=auth_headers_org_a,
            json={"query": "indemnification defend hold harmless", "contract_id": c1["id"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["contract_id"] == c1["id"]
        assert data["items"][0]["contract_title"] == "Contract Alpha"

    def test_search_tenant_isolation(self, client, auth_headers_org_a, auth_headers_org_b):
        # Org A uploads sensitive proprietary contract
        secret_text = (
            "CONFIDENTIAL INITIATIVE AGREEMENT\n\n"
            "Project Codename: ZEUS_HYPERION_SECRET_9876.\n"
            "All specifications are proprietary and strictly confidential."
        )
        pdf = generate_pdf_bytes([secret_text])
        up_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("secret.pdf", pdf, "application/pdf")},
            data={"title": "Project Zeus Proprietary", "contract_type": "nda"},
        )
        assert up_res.status_code == 201

        # Org B attempts to search for Project Zeus
        res_b = client.post(
            "/api/v1/contracts/search",
            headers=auth_headers_org_b,
            json={"query": "ZEUS_HYPERION_SECRET_9876"},
        )
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["total"] == 0
        assert data_b["items"] == []

        # Org A searches for the same keyword and finds it
        res_a = client.post(
            "/api/v1/contracts/search",
            headers=auth_headers_org_a,
            json={"query": "ZEUS_HYPERION_SECRET_9876"},
        )
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["total"] == 1
        assert "ZEUS_HYPERION_SECRET_9876" in data_a["items"][0]["snippet"]

    def test_search_unauthenticated(self, client):
        res = client.post("/api/v1/contracts/search", json={"query": "liability"})
        assert res.status_code == 401


class TestAuditLogsAPI:
    """Tests for GET /api/v1/audit."""

    def test_audit_log_retrieval(self, client, auth_headers_org_a):
        # Perform an upload to generate audit entries
        text = "AUDIT TEST CONTRACT\n\nSection 1. Terms."
        pdf = generate_pdf_bytes([text])
        client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("audit_c.pdf", pdf, "application/pdf")},
            data={"title": "Audit Test Contract", "contract_type": "service"},
        )

        res = client.get("/api/v1/audit", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] > 0
        assert len(data["items"]) > 0

        # Check required fields
        first_log = data["items"][0]
        assert "id" in first_log
        assert "action" in first_log
        assert "entity_type" in first_log
        assert "created_at" in first_log
        assert "user_name" in first_log
        assert first_log["user_name"] == "Counsel Alpha"

    def test_audit_log_action_filter(self, client, auth_headers_org_a):
        # Retrieve logs filtered by action
        res = client.get("/api/v1/audit?action=create", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        for log in data["items"]:
            assert log["action"].lower() == "create"

    def test_audit_log_pagination(self, client, auth_headers_org_a):
        res = client.get("/api/v1/audit?skip=0&limit=1", headers=auth_headers_org_a)
        assert res.status_code == 200
        data = res.json()
        assert data["skip"] == 0
        assert data["limit"] == 1
        assert len(data["items"]) <= 1

    def test_audit_log_tenant_isolation(self, client, auth_headers_org_a, auth_headers_org_b):
        # Org A performs a specific contract upload
        text_a = "ORGANIZATION A SPECIAL CONTRACT"
        pdf_a = generate_pdf_bytes([text_a])
        client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("org_a.pdf", pdf_a, "application/pdf")},
            data={"title": "Org A Unique Contract Title", "contract_type": "vendor"},
        )

        # Org B queries audit logs
        res_b = client.get("/api/v1/audit", headers=auth_headers_org_b)
        assert res_b.status_code == 200
        data_b = res_b.json()

        # Ensure Org B sees none of Org A's audit logs or user details
        for log in data_b["items"]:
            assert log["user_name"] != "Counsel Alpha"
            if log.get("details") and isinstance(log["details"], dict):
                assert log["details"].get("title") != "Org A Unique Contract Title"

    def test_audit_log_unauthenticated(self, client):
        res = client.get("/api/v1/audit")
        assert res.status_code == 401
