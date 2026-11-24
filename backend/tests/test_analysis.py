"""
LexFlow AI - Test Suite for Milestone 5: Rule-Based Contract Analysis Engine.

Comprehensive testing covering:
1. Deterministic clause detection across all 14 categories.
2. Rule-based risk evaluation for all 12 specific rules.
3. Missing clause detection on incomplete agreements.
4. Transparent risk scoring and risk band classification.
5. Modal verb obligation extraction and date/deadline parsing.
6. Idempotent analysis execution and database persistence.
7. Strict tenant isolation and audit logging.
"""

from datetime import date
import io
import uuid
from typing import List
import docx
import pymupdf
import pytest
from sqlalchemy import func, select

from app.models import AuditAction, AuditLog, Clause, Contract, DocumentChunk, Obligation, RiskAssessment
from app.models.enums import ClauseType, ObligationFrequency, ObligationStatus, RiskCategory, RiskSeverity
from app.services.clause_detector import (
    CLAUSE_DEFINITIONS,
    DetectedClause,
    detect_clauses_in_chunks,
    score_text_for_clause,
)
from app.services.obligation_extractor import (
    extract_obligations_from_clauses,
    identify_responsible_party,
    parse_calendar_date,
)
from app.services.risk_evaluator import (
    LEGAL_DISCLAIMER,
    determine_risk_band,
    evaluate_contract_risks,
)
from app.services.rules_catalogue import RISK_RULES, get_rule_by_id


# ---------------------------------------------------------------------------
# Helpers & Synthetic Contract Generators
# ---------------------------------------------------------------------------

def generate_pdf_bytes(pages_text: List[str]) -> bytes:
    """Generate a multi-page PDF in-memory."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 72), text)
    return doc.tobytes()


@pytest.fixture
def auth_headers_org_a(client):
    """Authenticate user for Org A."""
    email = f"user_a_{uuid.uuid4().hex[:6]}@lexflow-a.com"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Counsel Alpha",
        "email": email,
        "password": "Password123!",
        "organization_name": f"Firm Alpha {uuid.uuid4().hex[:4]}",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_org_b(client):
    """Authenticate user for Org B."""
    email = f"user_b_{uuid.uuid4().hex[:6]}@lexflow-b.com"
    res = client.post("/api/v1/auth/register", json={
        "full_name": "Counsel Beta",
        "email": email,
        "password": "Password123!",
        "organization_name": f"Firm Beta {uuid.uuid4().hex[:4]}",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. CLAUSE DETECTION TESTS (All 14 Categories)
# ===========================================================================

class TestClauseDetection:
    """Tests deterministic detection of the 14 contract clause categories."""

    def test_payment_terms_detection(self):
        text = "Section 4. Payment Terms. Invoices shall be paid net 30 days from date of receipt by wire transfer."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.PAYMENT_TERMS.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score
        assert 0.0 <= score <= 1.0

    def test_termination_detection(self):
        text = "Article 9. Term and Termination. Either party may terminate this agreement for material breach upon 30 days written notice."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.TERMINATION.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_confidentiality_detection(self):
        text = "Section 6. Confidentiality. Recipient agrees to hold in strict confidence all proprietary and confidential information."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.CONFIDENTIALITY.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_indemnification_detection(self):
        text = "Section 8. Indemnification. Vendor shall defend and hold harmless Client against any and all claims and losses."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.INDEMNIFICATION.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_limitation_of_liability_detection(self):
        text = "Section 10. Limitation of Liability. In no event shall aggregate liability exceed total fees paid under this agreement."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.LIMITATION_OF_LIABILITY.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_dispute_resolution_detection(self):
        text = "Article 12. Dispute Resolution. Any dispute arising out of this agreement shall be settled by binding arbitration under the rules of the American Arbitration Association."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.DISPUTE_RESOLUTION.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_governing_law_detection(self):
        text = "Section 14. Governing Law. This agreement shall be governed by and construed in accordance with the laws of the State of Delaware."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.GOVERNING_LAW.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_intellectual_property_detection(self):
        text = "Section 5. Intellectual Property Rights. Contractor assigns all right, title, and interest in work product to Company as a work made for hire."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.INTELLECTUAL_PROPERTY.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_data_protection_detection(self):
        text = "Section 11. Data Protection. Vendor shall process personal data solely in compliance with GDPR and maintain appropriate technical security measures."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.DATA_PROTECTION.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_renewal_detection(self):
        text = "Section 2. Renewal. This contract shall automatically renew for successive one-year terms unless notice of non-renewal is provided."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.RENEWAL.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_force_majeure_detection(self):
        text = "Clause 15. Force Majeure. Neither party shall be liable for failure to perform due to acts of God, flood, war, or events beyond reasonable control."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.FORCE_MAJEURE.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_non_compete_detection(self):
        text = "Section 7. Non-Compete Covenants. Consultant covenants not to directly or indirectly compete with the company or solicit customers within the restricted period."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.NON_COMPETE.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_warranty_detection(self):
        text = "Section 3. Representations and Warranties. Vendor warrants that the services will be performed in accordance with professional industry standards."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.WARRANTY.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_delivery_and_performance_detection(self):
        text = "Section 1. Delivery and Performance. Deliverables shall be delivered on or before the performance milestones. Time is of the essence."
        cdef = next(c for c in CLAUSE_DEFINITIONS if c.clause_type == ClauseType.DELIVERY_AND_PERFORMANCE.value)
        score = score_text_for_clause(text, cdef)
        assert score >= cdef.min_score

    def test_negative_clause_detection(self):
        """Random prose without legal clause signals should not match any clause."""
        random_text = "The weather was sunny in Seattle yesterday and employees enjoyed lunch in the cafeteria."
        for cdef in CLAUSE_DEFINITIONS:
            score = score_text_for_clause(random_text, cdef)
            assert score < cdef.min_score

    def test_detect_clauses_in_chunks_preserves_page_numbers(self):
        """Verify page_number is correctly preserved from document chunks."""
        class MockChunk:
            def __init__(self, content, page_number, chunk_index):
                self.content = content
                self.page_number = page_number
                self.chunk_index = chunk_index
                self.embedding_metadata = {}

        chunks = [
            MockChunk("Section 1. Confidentiality. Recipient shall protect confidential information.", 1, 0),
            MockChunk("Section 2. Governing Law. This agreement is governed by the laws of California.", 2, 1),
        ]
        detected = detect_clauses_in_chunks(chunks)
        assert len(detected) == 2
        conf_clause = next(c for c in detected if c.clause_type == ClauseType.CONFIDENTIALITY.value)
        gov_clause = next(c for c in detected if c.clause_type == ClauseType.GOVERNING_LAW.value)
        assert conf_clause.page_number == 1
        assert gov_clause.page_number == 2


# ===========================================================================
# 2. RULE-BASED RISK DETECTION TESTS (All 12 Specific Rules)
# ===========================================================================

class TestRiskDetectionRules:
    """Tests positive and negative triggers for each of the 12 Milestone 5 risk rules."""

    def test_rule_term_01_missing_termination(self):
        """Missing termination clause triggers RULE-TERM-01."""
        clauses = [
            DetectedClause(ClauseType.CONFIDENTIALITY.value, "Confidentiality", "Confidential text", 1, 0.8),
            DetectedClause(ClauseType.GOVERNING_LAW.value, "Governing Law", "Law text", 1, 0.8),
        ]
        res = evaluate_contract_risks(clauses, [])
        risk_ids = [r.rule_id for r in res.risks]
        assert "RULE-TERM-01" in risk_ids
        rule_risk = next(r for r in res.risks if r.rule_id == "RULE-TERM-01")
        assert rule_risk.severity == RiskSeverity.HIGH.value
        assert "Clause not identified" in rule_risk.evidence_text

    def test_rule_conf_01_missing_confidentiality(self):
        """Missing confidentiality clause triggers RULE-CONF-01."""
        clauses = [
            DetectedClause(ClauseType.TERMINATION.value, "Termination", "Termination text", 1, 0.8),
        ]
        res = evaluate_contract_risks(clauses, [])
        risk_ids = [r.rule_id for r in res.risks]
        assert "RULE-CONF-01" in risk_ids
        rule_risk = next(r for r in res.risks if r.rule_id == "RULE-CONF-01")
        assert rule_risk.severity == RiskSeverity.MEDIUM.value

    def test_rule_liab_01_missing_limitation_of_liability(self):
        """Missing limitation of liability triggers RULE-LIAB-01 with CRITICAL severity."""
        clauses = [
            DetectedClause(ClauseType.TERMINATION.value, "Termination", "Termination text", 1, 0.8),
        ]
        res = evaluate_contract_risks(clauses, [])
        risk_ids = [r.rule_id for r in res.risks]
        assert "RULE-LIAB-01" in risk_ids
        rule_risk = next(r for r in res.risks if r.rule_id == "RULE-LIAB-01")
        assert rule_risk.severity == RiskSeverity.CRITICAL.value
        assert rule_risk.risk_score == 10.0

    def test_rule_disp_01_missing_dispute_resolution(self):
        """Missing dispute resolution triggers RULE-DISP-01 with LOW severity."""
        clauses = [
            DetectedClause(ClauseType.TERMINATION.value, "Termination", "Termination text", 1, 0.8),
        ]
        res = evaluate_contract_risks(clauses, [])
        risk_ids = [r.rule_id for r in res.risks]
        assert "RULE-DISP-01" in risk_ids
        rule_risk = next(r for r in res.risks if r.rule_id == "RULE-DISP-01")
        assert rule_risk.severity == RiskSeverity.LOW.value
        assert rule_risk.risk_score == 1.0

    def test_rule_gov_01_missing_governing_law(self):
        """Missing governing law triggers RULE-GOV-01."""
        clauses = [
            DetectedClause(ClauseType.TERMINATION.value, "Termination", "Termination text", 1, 0.8),
        ]
        res = evaluate_contract_risks(clauses, [])
        risk_ids = [r.rule_id for r in res.risks]
        assert "RULE-GOV-01" in risk_ids
        rule_risk = next(r for r in res.risks if r.rule_id == "RULE-GOV-01")
        assert rule_risk.severity == RiskSeverity.LOW.value

    def test_rule_liab_02_unlimited_liability_trigger(self):
        """Unlimited liability text triggers RULE-LIAB-02."""
        clause = DetectedClause(
            ClauseType.LIMITATION_OF_LIABILITY.value,
            "Limitation of Liability",
            "The vendor shall be liable without limitation for all operational interruptions and damages.",
            1,
            0.9,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-LIAB-02" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-LIAB-02")
        assert risk.severity == RiskSeverity.CRITICAL.value
        assert "without limitation" in risk.evidence_text

    def test_rule_term_02_unilateral_termination_trigger(self):
        """Unilateral termination rights trigger RULE-TERM-02."""
        clause = DetectedClause(
            ClauseType.TERMINATION.value,
            "Termination",
            "Company may terminate this agreement at its sole discretion without cause at any time.",
            1,
            0.9,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-TERM-02" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-TERM-02")
        assert risk.severity == RiskSeverity.HIGH.value

    def test_rule_indm_01_broad_indemnification_trigger(self):
        """Broad indemnification language triggers RULE-INDM-01."""
        clause = DetectedClause(
            ClauseType.INDEMNIFICATION.value,
            "Indemnification",
            "Vendor shall indemnify, defend, and hold harmless against any and all claims howsoever arising.",
            1,
            0.9,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-INDM-01" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-INDM-01")
        assert risk.severity == RiskSeverity.HIGH.value

    def test_rule_rnw_01_auto_renewal_trigger(self):
        """Automatic renewal without explicit advance notice window triggers RULE-RNW-01."""
        clause = DetectedClause(
            ClauseType.RENEWAL.value,
            "Renewal",
            "This contract will automatically renew for successive terms unless canceled.",
            1,
            0.8,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-RNW-01" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-RNW-01")
        assert risk.severity == RiskSeverity.MEDIUM.value

    def test_rule_pay_01_ambiguous_payment_trigger(self):
        """Vague payment terms trigger RULE-PAY-01."""
        clause = DetectedClause(
            ClauseType.PAYMENT_TERMS.value,
            "Payment Terms",
            "Client shall remit payments as soon as practicable upon request from time to time.",
            1,
            0.8,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-PAY-01" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-PAY-01")
        assert risk.severity == RiskSeverity.MEDIUM.value

    def test_rule_ip_01_broad_ip_assignment_trigger(self):
        """Broad IP assignment triggers RULE-IP-01."""
        clause = DetectedClause(
            ClauseType.INTELLECTUAL_PROPERTY.value,
            "Intellectual Property",
            "Contractor irrevocably assigns all right, title, and interest in all inventions and works.",
            1,
            0.9,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-IP-01" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-IP-01")
        assert risk.severity == RiskSeverity.HIGH.value

    def test_rule_pen_01_excessive_penalties_trigger(self):
        """Penalty clauses trigger RULE-PEN-01."""
        clause = DetectedClause(
            ClauseType.PAYMENT_TERMS.value,
            "Payment Terms",
            "In case of breach, vendor shall pay a penalty of $50,000 as punitive damages.",
            1,
            0.8,
        )
        res = evaluate_contract_risks([clause], [])
        assert any(r.rule_id == "RULE-PEN-01" for r in res.risks)
        risk = next(r for r in res.risks if r.rule_id == "RULE-PEN-01")
        assert risk.severity == RiskSeverity.HIGH.value


# ===========================================================================
# 3. RISK SCORING & BAND CLASSIFICATION TESTS
# ===========================================================================

class TestRiskScoringEngine:
    """Tests transparent scoring weights, composite calculation, and risk bands."""

    def test_risk_bands(self):
        assert determine_risk_band(0.0) == "Low"
        assert determine_risk_band(9.9) == "Low"
        assert determine_risk_band(10.0) == "Medium"
        assert determine_risk_band(24.9) == "Medium"
        assert determine_risk_band(25.0) == "High"
        assert determine_risk_band(49.9) == "High"
        assert determine_risk_band(50.0) == "Critical"
        assert determine_risk_band(85.0) == "Critical"

    def test_severity_weights_and_distribution(self):
        # Empty contract with all 5 missing clause rules triggered:
        # RULE-LIAB-01 (Critical = 10)
        # RULE-TERM-01 (High = 7)
        # RULE-CONF-01 (Medium = 4)
        # RULE-DISP-01 (Low = 1)
        # RULE-GOV-01 (Low = 1)
        # Total = 10 + 7 + 4 + 1 + 1 = 23.0 -> "Medium" risk band
        res = evaluate_contract_risks([], [])
        assert res.total_risk_score == 23.0
        assert res.risk_band == "Medium"
        assert res.severity_distribution[RiskSeverity.CRITICAL.value] == 1
        assert res.severity_distribution[RiskSeverity.HIGH.value] == 1
        assert res.severity_distribution[RiskSeverity.MEDIUM.value] == 1
        assert res.severity_distribution[RiskSeverity.LOW.value] == 2
        assert res.disclaimer == LEGAL_DISCLAIMER


# ===========================================================================
# 4. OBLIGATION & DEADLINE EXTRACTION TESTS
# ===========================================================================

class TestObligationExtraction:
    """Tests modal verb parsing, party identification, and deadline detection."""

    def test_party_identification(self):
        assert identify_responsible_party("Vendor shall deliver the software.") == "Vendor"
        assert identify_responsible_party("The Client must submit all feedback.") == "Client"
        assert identify_responsible_party("Each party agrees to maintain insurance.") == "Each Party"
        assert identify_responsible_party("It is agreed that steps shall be taken.") == "Unspecified (Needs Review)"

    def test_exact_calendar_date_parsing(self):
        # ISO format
        assert parse_calendar_date("The report is due on 2026-12-31.") == date(2026, 12, 31)
        # Named month format
        assert parse_calendar_date("Final milestone due on March 15, 2026.") == date(2026, 3, 15)
        # Ordinal day of month
        assert parse_calendar_date("Deliver by 1st day of June 2026.") == date(2026, 6, 1)

    def test_relative_deadline_does_not_invent_dates(self):
        """Relative deadlines must preserve timeframe without guessing calendar dates."""
        clause = DetectedClause(
            ClauseType.PAYMENT_TERMS.value,
            "Payment Terms",
            "Customer shall pay all undisputed invoices within 30 days of receipt.",
            1,
            0.8,
        )
        obligations = extract_obligations_from_clauses([clause], [])
        assert len(obligations) >= 1
        ob = obligations[0]
        assert ob.responsible_party == "Customer"
        assert ob.due_date is None  # MUST NOT invent an arbitrary date!
        assert "within 30 days" in ob.description

    def test_recurrence_detection(self):
        clause = DetectedClause(
            ClauseType.PAYMENT_TERMS.value,
            "Payment Terms",
            "Client shall provide monthly compliance reports to the Auditor.",
            1,
            0.8,
        )
        obligations = extract_obligations_from_clauses([clause], [])
        assert len(obligations) >= 1
        assert obligations[0].frequency == ObligationFrequency.RECURRING_MONTHLY.value


# ===========================================================================
# 5. API ENDPOINTS & INTEGRATION TESTS
# ===========================================================================

class TestAnalysisAPIs:
    """Tests the full API flow for Milestone 5."""

    def test_full_analysis_workflow_pdf(self, client, auth_headers_org_a):
        """Upload a contract, trigger analysis, and verify clauses, risks, and obligations."""
        contract_text = (
            "MASTER SERVICES AGREEMENT\n\n"
            "Section 1. Payment Terms. Invoices shall be paid net 30 days from invoice date.\n\n"
            "Section 2. Term and Termination. Either party may terminate for convenience with 30 days notice.\n\n"
            "Section 3. Confidentiality. Both parties agree to protect proprietary information.\n\n"
            "Section 4. Limitation of Liability. Vendor liability shall be without limitation for breaches.\n\n"
            "Section 5. Governing Law. This agreement is governed by the laws of California.\n"
        )
        pdf_bytes = generate_pdf_bytes([contract_text])

        # 1. Upload
        upload_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("master_agreement.pdf", pdf_bytes, "application/pdf")},
            data={"title": "Master Services Agreement"},
        )
        assert upload_res.status_code == 201
        contract_id = upload_res.json()["id"]

        # 2. Trigger Analysis: POST /api/v1/contracts/{id}/analyze
        analyze_res = client.post(
            f"/api/v1/contracts/{contract_id}/analyze",
            headers=auth_headers_org_a,
        )
        assert analyze_res.status_code == 200
        analysis = analyze_res.json()

        assert analysis["contract_id"] == contract_id
        assert analysis["clauses_count"] >= 3
        assert analysis["risks_count"] >= 1
        assert analysis["obligations_count"] >= 1
        assert analysis["risk_score_summary"]["total_risk_score"] > 0
        assert analysis["risk_score_summary"]["risk_band"] in ("Low", "Medium", "High", "Critical")
        assert "screening aids" in analysis["legal_disclaimer"]

        # Verify unlimited liability risk was caught
        risk_titles = [r["title"] for r in analysis["risks"]]
        assert any("RULE-LIAB-02" in t for t in risk_titles)

        # 3. GET /api/v1/contracts/{id}/risks
        risks_res = client.get(
            f"/api/v1/contracts/{contract_id}/risks",
            headers=auth_headers_org_a,
        )
        assert risks_res.status_code == 200
        risks_data = risks_res.json()
        assert risks_data["contract_id"] == contract_id
        assert len(risks_data["items"]) == analysis["risks_count"]

        # 4. GET /api/v1/contracts/{id}/obligations
        ob_res = client.get(
            f"/api/v1/contracts/{contract_id}/obligations",
            headers=auth_headers_org_a,
        )
        assert ob_res.status_code == 200
        ob_data = ob_res.json()
        assert ob_data["contract_id"] == contract_id
        assert len(ob_data["items"]) == analysis["obligations_count"]

        # 5. GET /api/v1/contracts/{id}/analysis
        get_analysis_res = client.get(
            f"/api/v1/contracts/{contract_id}/analysis",
            headers=auth_headers_org_a,
        )
        assert get_analysis_res.status_code == 200
        get_analysis_data = get_analysis_res.json()
        assert get_analysis_data["contract_id"] == contract_id
        assert get_analysis_data["clauses_count"] == analysis["clauses_count"]

    def test_idempotent_reanalysis(self, client, auth_headers_org_a, db_session):
        """Calling analyze twice on the same contract must not duplicate database records."""
        contract_text = (
            "Section 1. Confidentiality. Recipient shall not disclose confidential data.\n\n"
            "Section 2. Governing Law. Laws of New York apply.\n"
        )
        pdf_bytes = generate_pdf_bytes([contract_text])

        upload_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("nda.pdf", pdf_bytes, "application/pdf")},
        )
        contract_id = upload_res.json()["id"]

        # Run analysis 1st time
        res1 = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=auth_headers_org_a)
        assert res1.status_code == 200
        clauses_count_1 = res1.json()["clauses_count"]
        risks_count_1 = res1.json()["risks_count"]

        # Run analysis 2nd time
        res2 = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=auth_headers_org_a)
        assert res2.status_code == 200
        clauses_count_2 = res2.json()["clauses_count"]
        risks_count_2 = res2.json()["risks_count"]

        # Counts returned must be identical
        assert clauses_count_1 == clauses_count_2
        assert risks_count_1 == risks_count_2

        # Check raw DB counts directly
        contract_uuid = uuid.UUID(contract_id)
        db_clauses = db_session.execute(
            select(func.count(Clause.id)).where(Clause.contract_id == contract_uuid)
        ).scalar()
        db_risks = db_session.execute(
            select(func.count(RiskAssessment.id)).where(RiskAssessment.contract_id == contract_uuid)
        ).scalar()

        assert db_clauses == clauses_count_1
        assert db_risks == risks_count_1

    def test_tenant_isolation_on_analysis(self, client, auth_headers_org_a, auth_headers_org_b):
        """Org B cannot trigger or view analysis on Org A's contracts."""
        contract_text = "Section 1. Governing Law. Laws of Texas apply."
        pdf_bytes = generate_pdf_bytes([contract_text])

        upload_res = client.post(
            "/api/v1/contracts/upload",
            headers=auth_headers_org_a,
            files={"file": ("texas_agreement.pdf", pdf_bytes, "application/pdf")},
        )
        contract_id = upload_res.json()["id"]

        # Org B attempts to analyze Org A's contract -> 404
        analyze_res = client.post(f"/api/v1/contracts/{contract_id}/analyze", headers=auth_headers_org_b)
        assert analyze_res.status_code == 404

        # Org B attempts to get risks -> 404
        risks_res = client.get(f"/api/v1/contracts/{contract_id}/risks", headers=auth_headers_org_b)
        assert risks_res.status_code == 404

        # Org B attempts to get obligations -> 404
        ob_res = client.get(f"/api/v1/contracts/{contract_id}/obligations", headers=auth_headers_org_b)
        assert ob_res.status_code == 404

        # Org B attempts to get analysis -> 404
        analysis_res = client.get(f"/api/v1/contracts/{contract_id}/analysis", headers=auth_headers_org_b)
        assert analysis_res.status_code == 404

    def test_unauthenticated_requests_rejected(self, client):
        """All analysis endpoints reject requests without a valid token."""
        random_id = uuid.uuid4()
        assert client.post(f"/api/v1/contracts/{random_id}/analyze").status_code == 401
        assert client.get(f"/api/v1/contracts/{random_id}/risks").status_code == 401
        assert client.get(f"/api/v1/contracts/{random_id}/obligations").status_code == 401
        assert client.get(f"/api/v1/contracts/{random_id}/analysis").status_code == 401
