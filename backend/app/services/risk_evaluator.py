"""
LexFlow AI - Deterministic Contract Risk Evaluator and Scoring Engine.

Evaluates contract chunks and detected clauses against the 12 rule catalogue checks.
Computes transparent risk scores, severity distributions, and assigns standardized risk bands.
Includes required legal screening disclaimers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re

from app.models.enums import RiskCategory, RiskSeverity, RiskStatus
from app.services.rules_catalogue import RISK_RULES, RiskRule
from app.services.clause_detector import DetectedClause


# Deterministic Severity Weights
SEVERITY_WEIGHTS: Dict[str, float] = {
    RiskSeverity.CRITICAL.value: 10.0,
    RiskSeverity.HIGH.value: 7.0,
    RiskSeverity.MEDIUM.value: 4.0,
    RiskSeverity.LOW.value: 1.0,
}

LEGAL_DISCLAIMER = (
    "LexFlow AI provides deterministic, rule-based legal screening aids to highlight "
    "potential contractual risks and obligations. Outputs are not legal advice, "
    "binding conclusions, or a substitute for professional legal review by qualified counsel."
)


@dataclass
class EvaluatedRisk:
    """Represents an identified risk finding ready for database persistence."""

    rule_id: str
    title: str
    description: str
    risk_score: float
    severity: str
    category: str
    mitigation_strategy: str
    evidence_text: Optional[str] = None
    target_clause_type: Optional[str] = None
    clause_index: Optional[int] = None  # Reference index into detected clauses list
    status: str = RiskStatus.IDENTIFIED.value


@dataclass
class RiskScoringResult:
    """Consolidated risk assessment scoring outcome."""

    total_risk_score: float
    risk_band: str  # "Low", "Medium", "High", "Critical"
    severity_distribution: Dict[str, int]
    total_risks_identified: int
    disclaimer: str = LEGAL_DISCLAIMER
    risks: List[EvaluatedRisk] = field(default_factory=list)


def determine_risk_band(total_score: float) -> str:
    """
    Maps total risk score to normalized risk bands:
    - 0 to 9: Low
    - 10 to 24: Medium
    - 25 to 49: High
    - 50+: Critical
    """
    if total_score >= 50.0:
        return "Critical"
    elif total_score >= 25.0:
        return "High"
    elif total_score >= 10.0:
        return "Medium"
    else:
        return "Low"


def extract_evidence_passage(text: str, match_obj: re.Match, window: int = 120) -> str:
    """Extracts a readable context snippet around a regex match."""
    start = max(0, match_obj.start() - window)
    end = min(len(text), match_obj.end() + window)
    snippet = text[start:end].strip().replace("\n", " ")
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def evaluate_contract_risks(
    detected_clauses: List[DetectedClause],
    raw_chunks: List[Any],
) -> RiskScoringResult:
    """
    Evaluates contract findings against the 12 rule catalogue checks:
    1. Evaluates missing clause rules against detected clause inventory.
    2. Evaluates pattern-match rules against detected clause texts and raw chunks.
    3. Calculates aggregate risk score and severity distribution.
    """
    identified_risks: List[EvaluatedRisk] = []
    seen_rule_matches = set()  # (rule_id, snippet_hash) to avoid duplicate risk logs

    # Set of detected clause types in the document
    detected_types = {c.clause_type for c in detected_clauses}

    # 1. Evaluate "missing_clause" rules
    for rule in RISK_RULES:
        if rule.rule_type == "missing_clause":
            if rule.target_clause_type and rule.target_clause_type not in detected_types:
                score = SEVERITY_WEIGHTS.get(rule.severity, 4.0)
                identified_risks.append(
                    EvaluatedRisk(
                        rule_id=rule.rule_id,
                        title=f"{rule.name} ({rule.rule_id})",
                        description=(
                            f"{rule.description}\n\n"
                            f"Finding: Clause of type '{rule.target_clause_type}' was not identified in the document."
                        ),
                        risk_score=score,
                        severity=rule.severity,
                        category=rule.category,
                        mitigation_strategy=rule.recommended_action,
                        evidence_text="Clause not identified in document.",
                        target_clause_type=rule.target_clause_type,
                        clause_index=None,
                    )
                )

    # 2. Evaluate "pattern_match" rules
    # First search within detected clauses (allows linking to clause)
    for c_idx, clause in enumerate(detected_clauses):
        for rule in RISK_RULES:
            if rule.rule_type == "pattern_match":
                compiled_patterns = rule.compile_patterns()
                for pattern in compiled_patterns:
                    match = pattern.search(clause.text)
                    if match:
                        evidence = extract_evidence_passage(clause.text, match)
                        sig = (rule.rule_id, evidence[:60])
                        if sig not in seen_rule_matches:
                            seen_rule_matches.add(sig)
                            score = SEVERITY_WEIGHTS.get(rule.severity, 4.0)
                            identified_risks.append(
                                EvaluatedRisk(
                                    rule_id=rule.rule_id,
                                    title=f"{rule.name} ({rule.rule_id})",
                                    description=(
                                        f"{rule.description}\n\n"
                                        f"Evidence excerpt: \"{evidence}\""
                                    ),
                                    risk_score=score,
                                    severity=rule.severity,
                                    category=rule.category,
                                    mitigation_strategy=rule.recommended_action,
                                    evidence_text=evidence,
                                    target_clause_type=clause.clause_type,
                                    clause_index=c_idx,
                                )
                            )
                            # Elevate clause risk level if risk is higher
                            if rule.severity in (RiskSeverity.HIGH.value, RiskSeverity.CRITICAL.value):
                                clause.risk_level = rule.severity
                        break

    # Next search across raw chunks for any text that wasn't classified as a clause
    for chunk in raw_chunks:
        content = getattr(chunk, "content", "") if hasattr(chunk, "content") else str(chunk)
        for rule in RISK_RULES:
            if rule.rule_type == "pattern_match":
                compiled_patterns = rule.compile_patterns()
                for pattern in compiled_patterns:
                    match = pattern.search(content)
                    if match:
                        evidence = extract_evidence_passage(content, match)
                        sig = (rule.rule_id, evidence[:60])
                        if sig not in seen_rule_matches:
                            seen_rule_matches.add(sig)
                            score = SEVERITY_WEIGHTS.get(rule.severity, 4.0)
                            identified_risks.append(
                                EvaluatedRisk(
                                    rule_id=rule.rule_id,
                                    title=f"{rule.name} ({rule.rule_id})",
                                    description=(
                                        f"{rule.description}\n\n"
                                        f"Evidence excerpt: \"{evidence}\""
                                    ),
                                    risk_score=score,
                                    severity=rule.severity,
                                    category=rule.category,
                                    mitigation_strategy=rule.recommended_action,
                                    evidence_text=evidence,
                                    target_clause_type=None,
                                    clause_index=None,
                                )
                            )
                        break

    # 3. Calculate aggregate score and severity distribution
    total_score = sum(r.risk_score for r in identified_risks)
    distribution = {
        RiskSeverity.CRITICAL.value: sum(1 for r in identified_risks if r.severity == RiskSeverity.CRITICAL.value),
        RiskSeverity.HIGH.value: sum(1 for r in identified_risks if r.severity == RiskSeverity.HIGH.value),
        RiskSeverity.MEDIUM.value: sum(1 for r in identified_risks if r.severity == RiskSeverity.MEDIUM.value),
        RiskSeverity.LOW.value: sum(1 for r in identified_risks if r.severity == RiskSeverity.LOW.value),
    }
    risk_band = determine_risk_band(total_score)

    return RiskScoringResult(
        total_risk_score=round(total_score, 1),
        risk_band=risk_band,
        severity_distribution=distribution,
        total_risks_identified=len(identified_risks),
        disclaimer=LEGAL_DISCLAIMER,
        risks=identified_risks,
    )
