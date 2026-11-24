"""
LexFlow AI - Deterministic Contract Risk Rules Catalogue.

Predefined, configurable rule definitions for rule-based legal risk screening.
Does NOT use LLMs, external APIs, or probabilistic machine learning models.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re

from app.models.enums import ClauseType, RiskCategory, RiskSeverity


@dataclass(frozen=True)
class RiskRule:
    """Represents a deterministic legal risk rule."""

    rule_id: str
    name: str
    category: str
    severity: str
    rule_type: str  # "missing_clause" or "pattern_match"
    target_clause_type: Optional[str] = None
    patterns: List[str] = field(default_factory=list)
    description: str = ""
    recommended_action: str = ""

    def compile_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns with IGNORECASE and DOTALL flags."""
        return [re.compile(p, re.IGNORECASE) for p in self.patterns]


# The 12 Specific Milestone 5 Risk Rules
RISK_RULES: List[RiskRule] = [
    # 1. Missing Termination Clause
    RiskRule(
        rule_id="RULE-TERM-01",
        name="Missing Termination Clause",
        category=RiskCategory.LEGAL.value,
        severity=RiskSeverity.HIGH.value,
        rule_type="missing_clause",
        target_clause_type=ClauseType.TERMINATION.value,
        description=(
            "The agreement lacks an identifiable termination clause. Without explicit exit terms, "
            "parties may face substantial difficulty terminating the relationship without common law breach claims."
        ),
        recommended_action=(
            "Review agreement with legal counsel and draft express termination for convenience and "
            "termination for material breach clauses with clearly defined cure periods."
        ),
    ),
    # 2. Missing Confidentiality Clause
    RiskRule(
        rule_id="RULE-CONF-01",
        name="Missing Confidentiality Clause",
        category=RiskCategory.LEGAL.value,
        severity=RiskSeverity.MEDIUM.value,
        rule_type="missing_clause",
        target_clause_type=ClauseType.CONFIDENTIALITY.value,
        description=(
            "The agreement does not contain an identified confidentiality or non-disclosure provision. "
            "Proprietary information, trade secrets, and business data exchanged may not be legally protected."
        ),
        recommended_action=(
            "Insert mutual confidentiality covenants defining proprietary information, permitted disclosures, "
            "and standard survival periods (e.g., 3-5 years post-termination)."
        ),
    ),
    # 3. Missing Limitation of Liability Clause
    RiskRule(
        rule_id="RULE-LIAB-01",
        name="Missing Limitation of Liability Clause",
        category=RiskCategory.FINANCIAL.value,
        severity=RiskSeverity.CRITICAL.value,
        rule_type="missing_clause",
        target_clause_type=ClauseType.LIMITATION_OF_LIABILITY.value,
        description=(
            "The agreement does not contain an explicit limitation of liability clause. "
            "This exposes the organization to uncapped direct, indirect, special, and consequential damages."
        ),
        recommended_action=(
            "Introduce an aggregate liability cap (e.g., total fees paid in prior 12 months) "
            "and a mutual disclaimer of consequential, punitive, and indirect damages."
        ),
    ),
    # 4. Missing Dispute Resolution Clause
    RiskRule(
        rule_id="RULE-DISP-01",
        name="Missing Dispute Resolution Clause",
        category=RiskCategory.LEGAL.value,
        severity=RiskSeverity.LOW.value,
        rule_type="missing_clause",
        target_clause_type=ClauseType.DISPUTE_RESOLUTION.value,
        description=(
            "No formal dispute resolution procedure (such as good-faith negotiation, mediation, or arbitration) "
            "was detected. Conflicts may lead directly to costly, protracted court litigation."
        ),
        recommended_action=(
            "Add a multi-tier dispute escalation clause specifying informal executive negotiation, "
            "followed by binding arbitration or specialized commercial mediation."
        ),
    ),
    # 5. Unlimited Liability Language
    RiskRule(
        rule_id="RULE-LIAB-02",
        name="Unlimited Liability Language",
        category=RiskCategory.FINANCIAL.value,
        severity=RiskSeverity.CRITICAL.value,
        rule_type="pattern_match",
        patterns=[
            r"\bwithout\s+limitation\b",
            r"\bunlimited\s+liability\b",
            r"\bno\s+cap\s+(?:on|to)\s+liability\b",
            r"\bshall\s+not\s+be\s+limited\b",
            r"\bliability\s+shall\s+be\s+unlimited\b",
            r"\bnotwithstanding\s+anything\s+to\s+the\s+contrary.*?(?:liability|indemnification)\s+shall\s+not\s+be\s+(?:capped|limited)\b",
            r"\bshall\s+have\s+unlimited\s+responsibility\b",
        ],
        description=(
            "Contract language suggests unbounded or uncapped financial liability exposure. "
            "Clauses containing 'without limitation' or 'shall not be limited' can nullify liability caps."
        ),
        recommended_action=(
            "Strictly qualify carve-outs from the liability cap to gross negligence, willful misconduct, "
            "and statutory obligations, ensuring operational claims remain subject to negotiated aggregate caps."
        ),
    ),
    # 6. Unilateral Termination Rights
    RiskRule(
        rule_id="RULE-TERM-02",
        name="Unilateral Termination Rights",
        category=RiskCategory.OPERATIONAL.value,
        severity=RiskSeverity.HIGH.value,
        rule_type="pattern_match",
        patterns=[
            r"\b(?:at\s+(?:its|their)\s+sole\s+discretion|sole\s+option\s+to\s+terminate)\b",
            r"\bwithout\s+cause\s+by\s+(?:company|vendor|client|customer|service\s+provider|licensor)\b",
            r"\bmay\s+terminate\s+(?:this\s+agreement\s+)?at\s+any\s+time\s+without\s+cause\b",
            r"\bsole\s+and\s+absolute\s+discretion\s+to\s+terminate\b",
            r"\bright\s+to\s+terminate\s+immediately\s+without\s+(?:notice|cause)\b",
        ],
        description=(
            "Language indicates one party possesses the unilateral or unrestricted right to terminate "
            "the agreement at will, creating operational volatility and asymmetric bargaining power."
        ),
        recommended_action=(
            "Negotiate mutual termination rights, minimum advance written notice requirements (e.g., 30-60 days), "
            "and reimbursement for unamortized investments or transition costs."
        ),
    ),
    # 7. Broad Indemnification Language
    RiskRule(
        rule_id="RULE-INDM-01",
        name="Broad Indemnification Language",
        category=RiskCategory.LEGAL.value,
        severity=RiskSeverity.HIGH.value,
        rule_type="pattern_match",
        patterns=[
            r"\bindemnify(?:,\s*defend)?\s*(?:,\s*and\s*hold\s*harmless)?\s*against\s*(?:any\s*and\s*all|all)\s*(?:claims|demands|losses)\b",
            r"\b(?:all|any\s*and\s*all)\s*losses,\s*damages,\s*liabilities,\s*costs,\s*(?:and\s*)?expenses,\s*including\s*attorneys['’]?\s*fees\b",
            r"\bhowsoever\s+arising\b",
            r"\bregardless\s+of\s+(?:the\s+)?cause\b",
            r"\bindemnify.*?from\s+any\s+and\s+all\s+third[- ]party\s+claims\b",
            r"\bindemnify.*?whether\s+arising\s+in\s+tort,\s+contract,\s+or\s+otherwise\b",
        ],
        description=(
            "Overly broad indemnification obligations identified. Language requiring defense and indemnification "
            "against 'any and all claims' or 'howsoever arising' forces assumption of risks outside direct control."
        ),
        recommended_action=(
            "Limit indemnification obligations strictly to direct third-party intellectual property infringement "
            "or gross negligence, and require prompt written notice and control of legal defense."
        ),
    ),
    # 8. Automatic Renewal Without Notice Period
    RiskRule(
        rule_id="RULE-RNW-01",
        name="Automatic Renewal Without Notice Period",
        category=RiskCategory.OPERATIONAL.value,
        severity=RiskSeverity.MEDIUM.value,
        rule_type="pattern_match",
        patterns=[
            r"\bautomatically\s+renew(?:s|ed|ing)?(?!\s+unless\s+(?:either\s+party\s+gives\s+)?(?:at\s+least\s+)?\d+\s+days)",
            r"\bauto[- ]renew(?:s|ed|ing)?(?!\s+unless\s+(?:either\s+party\s+gives\s+)?(?:at\s+least\s+)?\d+\s+days)",
            r"\brenew\s+for\s+successive\s+terms(?!\s+unless\s+(?:either\s+party\s+gives\s+)?(?:at\s+least\s+)?\d+\s+days)",
            r"\bautomatic(?:ally)?\s+extension\s+without\s+notice\b",
        ],
        description=(
            "Contract appears to automatically renew without an explicit, verifiable advance notice window, "
            "creating evergreen lock-in risk and unexpected recurring financial commitments."
        ),
        recommended_action=(
            "Establish a clear non-renewal notification window (e.g., at least 30 or 60 days prior to the end "
            "of the initial term) and set automated calendar reminders for contract review."
        ),
    ),
    # 9. Ambiguous Payment Deadlines
    RiskRule(
        rule_id="RULE-PAY-01",
        name="Ambiguous Payment Deadlines",
        category=RiskCategory.FINANCIAL.value,
        severity=RiskSeverity.MEDIUM.value,
        rule_type="pattern_match",
        patterns=[
            r"\bas\s+soon\s+as\s+practicable\b",
            r"\bupon\s+request\b",
            r"\bperiodically\b",
            r"\bfrom\s+time\s+to\s+time\b",
            r"\bpromptly\s+upon\s+receipt\b",
            r"\bpayable\s+at\s+(?:the\s+)?convenience\b",
            r"\bpaid\s+in\s+due\s+course\b",
        ],
        description=(
            "Payment timeline utilizes vague, subjective terms ('as soon as practicable', 'promptly upon receipt', "
            "'periodically') rather than a definitive calendar-day timeframe (e.g., Net 30 days)."
        ),
        recommended_action=(
            "Replace ambiguous payment triggers with precise Net payment terms (e.g., 'within 30 calendar days of invoice date') "
            "and specify dispute withholding procedures."
        ),
    ),
    # 10. Missing Governing Law Clause
    RiskRule(
        rule_id="RULE-GOV-01",
        name="Missing Governing Law Clause",
        category=RiskCategory.LEGAL.value,
        severity=RiskSeverity.LOW.value,
        rule_type="missing_clause",
        target_clause_type=ClauseType.GOVERNING_LAW.value,
        description=(
            "The agreement lacks an identifiable governing law and jurisdiction provision. "
            "Cross-border or multi-state disputes will incur significant legal fees litigating choice of law."
        ),
        recommended_action=(
            "Specify an agreed governing law jurisdiction and exclusive or non-exclusive forum venue "
            "familiar to the organization's legal team."
        ),
    ),
    # 11. Broad IP Assignment
    RiskRule(
        rule_id="RULE-IP-01",
        name="Broad IP Assignment",
        category=RiskCategory.LEGAL.value,
        severity=RiskSeverity.HIGH.value,
        rule_type="pattern_match",
        patterns=[
            r"\bassigns?\s+(?:all\s+)?right,\s*title,?\s*and\s*interest\b",
            r"\birrevocably\s+assigns?\s+all\s+(?:inventions|works|developments|concepts|ip)\b",
            r"\bwork\s+(?:made\s+)?for\s+hire.*?including\s+all\s+moral\s+rights\b",
            r"\bsole\s+and\s+exclusive\s+property\s+of\s+(?:company|client|customer)\s+without\s+exception\b",
            r"\bhereby\s+assigns?\s+all\s+present\s+and\s+future\s+intellectual\s+property\b",
            r"\btransfer\s+all\s+intellectual\s+property\s+rights\s+in\s+any\s+and\s+all\s+works\b",
        ],
        description=(
            "Broad intellectual property assignment language detected. Terms transferring 'all right, title, and interest' "
            "or including 'moral rights' and background IP can jeopardize pre-existing proprietary technology and tools."
        ),
        recommended_action=(
            "Explicitly carve out Background Intellectual Property, pre-existing tools, open-source libraries, "
            "and grant a non-exclusive license rather than an absolute ownership assignment where appropriate."
        ),
    ),
    # 12. Excessive Contractual Penalties
    RiskRule(
        rule_id="RULE-PEN-01",
        name="Excessive Contractual Penalties",
        category=RiskCategory.FINANCIAL.value,
        severity=RiskSeverity.HIGH.value,
        rule_type="pattern_match",
        patterns=[
            r"\bpenalty\s+of\b",
            r"\bpunitive\s+damages\b",
            r"\bliquidated\s+damages\s+(?:in\s+the\s+amount\s+of|exceeding)\b",
            r"\bforfeit\s+all\s+(?:compensation|fees|deposits)\b",
            r"\bimmediate\s+forfeiture\b",
            r"\binterest\s+rate\s+of\s+(?:[2-9]\d|1\d{2})%\b",  # Interest rates >= 20%
            r"\bpay\s+as\s+a\s+penalty\b",
        ],
        description=(
            "Contract clauses stipulate punitive damages, contract penalties, or immediate forfeiture. "
            "In many jurisdictions, punitive penalty clauses are legally unenforceable and create disproportionate financial risk."
        ),
        recommended_action=(
            "Eliminate explicit penalty clauses; ensure any liquidated damages represent a genuine, pre-estimated "
            "forecast of actual losses rather than a punitive deterrent, or cap late payment interest to statutory maximums."
        ),
    ),
]


def get_rule_by_id(rule_id: str) -> Optional[RiskRule]:
    """Look up a risk rule by its unique identifier."""
    for rule in RISK_RULES:
        if rule.rule_id == rule_id:
            return rule
    return None
