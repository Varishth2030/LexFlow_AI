"""
Services Package.

Provides business logic utilities, document processing, and external integration hooks.
"""

from app.services.document_processor import (
    compute_file_hash,
    process_docx,
    process_pdf,
    save_upload_file,
    validate_file_format_and_size,
)
from app.services.rules_catalogue import RISK_RULES, RiskRule, get_rule_by_id
from app.services.clause_detector import (
    CLAUSE_DEFINITIONS,
    DetectedClause,
    detect_clauses_in_chunks,
    score_text_for_clause,
)
from app.services.risk_evaluator import (
    LEGAL_DISCLAIMER,
    EvaluatedRisk,
    RiskScoringResult,
    determine_risk_band,
    evaluate_contract_risks,
)
from app.services.obligation_extractor import (
    ExtractedObligation,
    extract_obligations_from_clauses,
    parse_calendar_date,
)
from app.services.contract_analyzer import analyze_contract
from app.services.compliance_service import (
    build_control_response,
    build_task_response,
    check_and_update_overdue,
    compute_compliance_dashboard,
    validate_task_related_entities,
)

__all__ = [
    "validate_file_format_and_size",
    "process_pdf",
    "process_docx",
    "save_upload_file",
    "compute_file_hash",
    "RISK_RULES",
    "RiskRule",
    "get_rule_by_id",
    "CLAUSE_DEFINITIONS",
    "DetectedClause",
    "detect_clauses_in_chunks",
    "score_text_for_clause",
    "LEGAL_DISCLAIMER",
    "EvaluatedRisk",
    "RiskScoringResult",
    "determine_risk_band",
    "evaluate_contract_risks",
    "ExtractedObligation",
    "extract_obligations_from_clauses",
    "parse_calendar_date",
    "analyze_contract",
    "validate_task_related_entities",
    "check_and_update_overdue",
    "build_task_response",
    "build_control_response",
    "compute_compliance_dashboard",
]
