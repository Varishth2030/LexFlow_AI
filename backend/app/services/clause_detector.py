"""
LexFlow AI - Deterministic Clause Detection Service.

Rule-based clause identification using regular expressions, heading parsing,
and keyword density. Preserves page and paragraph references without LLMs or external APIs.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re

from app.models.enums import ClauseType, RiskSeverity


@dataclass
class DetectedClause:
    """Represents a deterministically detected clause."""

    clause_type: str
    title: str
    text: str
    page_number: Optional[int]
    rule_match_indicator: float  # Deterministic score (0.0 - 1.0) based on pattern matches
    risk_level: str = RiskSeverity.LOW.value
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ClauseDefinition:
    """Definition for a clause type with patterns and scoring criteria."""

    clause_type: str
    title: str
    heading_patterns: List[str]
    body_patterns: List[str]
    keywords: List[str]
    min_score: float = 0.40


CLAUSE_DEFINITIONS: List[ClauseDefinition] = [
    # 1. Payment Terms
    ClauseDefinition(
        clause_type=ClauseType.PAYMENT_TERMS.value,
        title="Payment Terms",
        heading_patterns=[
            r"\b(?:payment(?:\s+terms)?|fees?\s+and\s+expenses?|pricing|invoicing|compensation|billing)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:payment|fees|invoicing)",
        ],
        body_patterns=[
            r"\bnet\s+(?:15|30|45|60|90)\s+(?:days|calendar\s+days|business\s+days)\b",
            r"\bpayable\s+within\s+\d+\s+days\b",
            r"\binvoices?\s+shall\s+be\s+paid\b",
            r"\bwire\s+transfer|electronic\s+funds\s+transfer|ach\b",
            r"\blate\s+payment\s+(?:charge|interest|fee)\b",
            r"\bfees?\s+(?:payable|due)\s+under\s+this\s+agreement\b",
        ],
        keywords=["payment", "invoice", "fee", "fees", "billing", "due date", "remit", "reimbursement", "currency"],
    ),
    # 2. Termination
    ClauseDefinition(
        clause_type=ClauseType.TERMINATION.value,
        title="Termination",
        heading_patterns=[
            r"\b(?:term\s+and\s+termination|termination|cancellation|expiration|termination\s+for\s+cause)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:termination|term)",
        ],
        body_patterns=[
            r"\bterminate\s+this\s+agreement\b",
            r"\btermination\s+for\s+(?:cause|convenience|material\s+breach)\b",
            r"\beither\s+party\s+may\s+terminate\b",
            r"\bwritten\s+notice\s+of\s+termination\b",
            r"\bupon\s+termination\s+or\s+expiration\b",
            r"\bcure\s+period\s+of\s+\d+\s+days\b",
        ],
        keywords=["terminate", "termination", "cure period", "material breach", "convenience", "notice of default", "expiration"],
    ),
    # 3. Confidentiality
    ClauseDefinition(
        clause_type=ClauseType.CONFIDENTIALITY.value,
        title="Confidentiality",
        heading_patterns=[
            r"\b(?:confidentiality|non[- ]disclosure|proprietary\s+information|confidential\s+information)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:confidentiality|non[- ]disclosure)",
        ],
        body_patterns=[
            r"\bconfidential\s+information\s+(?:shall|means|includes)\b",
            r"\bnon[- ]disclosure\s+agreement\b",
            r"\bhold\s+in\s+strict\s+confidence\b",
            r"\bshall\s+not\s+disclose\s+(?:to\s+any\s+third\s+party|such\s+information)\b",
            r"\brecipient\s+agrees\s+to\s+protect\b",
            r"\bproprietary\s+and\s+confidential\b",
        ],
        keywords=["confidential", "proprietary", "trade secret", "non-disclosure", "disclose", "recipient", "disclosing party"],
    ),
    # 4. Indemnification
    ClauseDefinition(
        clause_type=ClauseType.INDEMNIFICATION.value,
        title="Indemnification",
        heading_patterns=[
            r"\b(?:indemnification|indemnity|defense\s+and\s+indemnity|hold\s+harmless)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:indemnification|indemnity)",
        ],
        body_patterns=[
            r"\bindemnify(?:,\s*defend)?\s*(?:,\s*and\s*hold\s*harmless)?\b",
            r"\bindemnified\s+party\b",
            r"\bagainst\s+any\s+and\s+all\s+(?:claims|losses|damages|liabilities)\b",
            r"\bdefend\s+at\s+its\s+sole\s+expense\b",
            r"\bhold\s+harmless\s+from\s+and\s+against\b",
        ],
        keywords=["indemnify", "indemnification", "indemnity", "hold harmless", "defend", "losses", "third-party claim"],
    ),
    # 5. Limitation of Liability
    ClauseDefinition(
        clause_type=ClauseType.LIMITATION_OF_LIABILITY.value,
        title="Limitation of Liability",
        heading_patterns=[
            r"\b(?:limitation\s+of\s+liability|limit\s+of\s+liability|aggregate\s+liability|consequential\s+damages)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:limitation\s+of\s+liability|liability)",
        ],
        body_patterns=[
            r"\b(?:in\s+no\s+event\s+shall|neither\s+party\s+shall\s+be\s+liable\s+for)\b",
            r"\b(?:indirect|incidental|consequential|punitive|special)\s+damages\b",
            r"\baggregate\s+liability\s+(?:shall\s+not\s+exceed|capped\s+at)\b",
            r"\blimitation\s+of\s+liability\b",
            r"\bmaximum\s+cumulative\s+liability\b",
            r"\btotal\s+fees\s+paid\s+(?:or\s+payable\s+)?under\s+this\s+agreement\b",
        ],
        keywords=["limitation of liability", "consequential damages", "aggregate liability", "incidental damages", "exceed", "cap"],
    ),
    # 6. Dispute Resolution
    ClauseDefinition(
        clause_type=ClauseType.DISPUTE_RESOLUTION.value,
        title="Dispute Resolution",
        heading_patterns=[
            r"\b(?:dispute\s+resolution|arbitration|mediation|escalation|settlement\s+of\s+disputes)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:dispute\s+resolution|arbitration)",
        ],
        body_patterns=[
            r"\bbinding\s+arbitration\b",
            r"\brules\s+of\s+the\s+(?:american\s+arbitration\s+association|aaa|icc|jams|lcia)\b",
            r"\bmediation\s+(?:prior\s+to|before)\s+litigation\b",
            r"\bdispute\s+arising\s+out\s+of\s+or\s+in\s+connection\s+with\b",
            r"\bescalat(?:e|ion)\s+to\s+senior\s+executives\b",
            r"\bexclusive\s+jurisdiction\s+to\s+resolve\s+any\s+dispute\b",
        ],
        keywords=["dispute", "arbitration", "arbitrator", "mediation", "mediator", "jams", "aaa", "settlement"],
    ),
    # 7. Governing Law
    ClauseDefinition(
        clause_type=ClauseType.GOVERNING_LAW.value,
        title="Governing Law",
        heading_patterns=[
            r"\b(?:governing\s+law|applicable\s+law|choice\s+of\s+law|jurisdiction\s+and\s+venue)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:governing\s+law|jurisdiction)",
        ],
        body_patterns=[
            r"\bgoverned\s+by\s+and\s+construed\s+in\s+accordance\s+with\s+the\s+laws\s+of\b",
            r"\bwithout\s+regard\s+to\s+(?:its\s+)?conflict\s+of\s+law\s+principles\b",
            r"\bexclusive\s+jurisdiction\s+of\s+the\s+courts\s+of\b",
            r"\bvenue\s+shall\s+lie\s+(?:exclusively\s+)?in\b",
            r"\bsubmit\s+to\s+the\s+personal\s+jurisdiction\b",
        ],
        keywords=["governing law", "construed in accordance", "conflict of laws", "jurisdiction", "venue", "courts of"],
    ),
    # 8. Intellectual Property
    ClauseDefinition(
        clause_type=ClauseType.INTELLECTUAL_PROPERTY.value,
        title="Intellectual Property",
        heading_patterns=[
            r"\b(?:intellectual\s+property|ip\s+rights|ownership|proprietary\s+rights|patents\s+and\s+copyrights|work\s+product)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:intellectual\s+property|ownership|ip\s+rights)",
        ],
        body_patterns=[
            r"\bintellectual\s+property\s+rights\b",
            r"\bpatents?,\s*copyrights?,\s*trademarks?,\s*(?:and\s*)?trade\s+secrets\b",
            r"\bassigns?\s+(?:all\s+)?right,\s*title,\s*and\s*interest\b",
            r"\bwork\s+(?:made\s+)?for\s+hire\b",
            r"\bbackground\s+(?:ip|intellectual\s+property)\b",
            r"\blicense\s+grant\b",
            r"\bretains\s+(?:all\s+)?sole\s+ownership\b",
        ],
        keywords=["intellectual property", "trademark", "patent", "copyright", "work for hire", "assignment", "license", "proprietary"],
    ),
    # 9. Data Protection
    ClauseDefinition(
        clause_type=ClauseType.DATA_PROTECTION.value,
        title="Data Protection",
        heading_patterns=[
            r"\b(?:data\s+protection|data\s+privacy|security\s+measures|personal\s+data|gdpr|information\s+security)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:data\s+protection|privacy|security)",
        ],
        body_patterns=[
            r"\bpersonal\s+data\s+or\s+personally\s+identifiable\s+information\b",
            r"\bcompliance\s+with\s+(?:gdpr|ccpa|hipaa|data\s+protection\s+laws)\b",
            r"\bdata\s+processing\s+addendum\b",
            r"\bsecurity\s+breach\s+notification\b",
            r"\bappropriate\s+technical\s+and\s+organizational\s+measures\b",
            r"\bprocess\s+personal\s+data\s+solely\s+on\s+behalf\s+of\b",
        ],
        keywords=["personal data", "gdpr", "privacy", "data processing", "security breach", "pii", "encryption"],
    ),
    # 10. Renewal
    ClauseDefinition(
        clause_type=ClauseType.RENEWAL.value,
        title="Renewal",
        heading_patterns=[
            r"\b(?:renewal|extension\s+of\s+term|automatic\s+renewal|renewal\s+term)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:renewal|extension)",
        ],
        body_patterns=[
            r"\bautomatically\s+renew(?:s|ed|ing)?\b",
            r"\brenew\s+for\s+successive\s+(?:one[- ]year|terms|periods)\b",
            r"\bnotice\s+of\s+non[- ]renewal\b",
            r"\beither\s+party\s+gives\s+written\s+notice\s+at\s+least\s+\d+\s+days\s+prior\b",
            r"\brenewal\s+period\s+shall\s+commence\b",
        ],
        keywords=["renewal", "auto-renew", "successive terms", "non-renewal", "extension", "anniversary date"],
    ),
    # 11. Force Majeure
    ClauseDefinition(
        clause_type=ClauseType.FORCE_MAJEURE.value,
        title="Force Majeure",
        heading_patterns=[
            r"\b(?:force\s+majeure|acts\s+of\s+god|unforeseen\s+circumstances|events\s+beyond\s+control)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:force\s+majeure)",
        ],
        body_patterns=[
            r"\bacts\s+of\s+god|natural\s+disasters?|earthquakes?|floods?|fires?\b",
            r"\bbeyond\s+the\s+reasonable\s+control\s+of\s+(?:such|either)\s+party\b",
            r"\bwar,\s*terrorism,\s*civil\s+unrest|epidemic|pandemic\b",
            r"\bexcused\s+from\s+performance\s+(?:during|by\s+reason\s+of)\b",
            r"\bforce\s+majeure\s+event\b",
        ],
        keywords=["force majeure", "acts of god", "natural disaster", "beyond reasonable control", "epidemic", "strike", "embargo"],
    ),
    # 12. Non-Compete
    ClauseDefinition(
        clause_type=ClauseType.NON_COMPETE.value,
        title="Non-Compete",
        heading_patterns=[
            r"\b(?:non[- ]compete|covenant\s+not\s+to\s+compete|non[- ]solicitation|restrictive\s+covenants)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:non[- ]compete|restrictive\s+covenants)",
        ],
        body_patterns=[
            r"\bshall\s+not\s+(?:directly\s+or\s+indirectly\s+)?compete\s+with\b",
            r"\bnon[- ]solicitation\s+of\s+(?:employees|customers|clients)\b",
            r"\brestricted\s+period\s+of\s+\d+\s+(?:months|years)\b",
            r"\bgeographic\s+territory|geographic\s+scope\b",
            r"\bengage\s+in\s+any\s+business\s+competitive\s+with\b",
        ],
        keywords=["non-compete", "non-solicitation", "competitive business", "restrictive covenant", "compete", "solicit"],
    ),
    # 13. Warranty
    ClauseDefinition(
        clause_type=ClauseType.WARRANTY.value,
        title="Warranty",
        heading_patterns=[
            r"\b(?:representations\s+and\s+warranties|warranty|warranties|disclaimer\s+of\s+warranties)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:warranties|representations)",
        ],
        body_patterns=[
            r"\brepresents\s+and\s+warrants\s+(?:that)?\b",
            r"\bwarrants\s+that\s+the\s+services\s+will\s+be\s+performed\b",
            r"\bas\s+is\s+without\s+warranty\b",
            r"\bexpress\s+or\s+implied\s+warranties\b",
            r"\bmerchantability\s+and\s+fitness\s+for\s+a\s+particular\s+purpose\b",
            r"\bconforms?\s+to\s+specifications\b",
        ],
        keywords=["warranty", "warranties", "representation", "merchantability", "fitness for purpose", "as is", "express warranty"],
    ),
    # 14. Delivery and Performance
    ClauseDefinition(
        clause_type=ClauseType.DELIVERY_AND_PERFORMANCE.value,
        title="Delivery and Performance",
        heading_patterns=[
            r"\b(?:delivery\s+and\s+performance|deliverables|performance\s+standards|service\s+levels|sla|milestones)\b",
            r"(?:section|clause|article)\s*\d*[\.\:]?\s*(?:deliverables|delivery|performance\s+standards)",
        ],
        body_patterns=[
            r"\bdeliverables\s+shall\s+be\s+delivered\b",
            r"\btime\s+is\s+of\s+the\s+essence\b",
            r"\bservice\s+level\s+agreements?|sla\s+target\b",
            r"\bacceptance\s+testing\s+and\s+inspection\b",
            r"\bperformance\s+milestones?\b",
            r"\bdelivered\s+on\s+or\s+before\b",
        ],
        keywords=["delivery", "deliverable", "milestone", "service level", "sla", "acceptance criteria", "performance standard"],
    ),
]


def score_text_for_clause(
    text: str,
    definition: ClauseDefinition,
) -> float:
    """
    Computes a deterministic rule-match indicator (0.0 to 1.0) for a given text snippet.
    Calculated via weighted regular expression heading matches, body pattern matches,
    and keyword density.
    """
    score = 0.0
    text_lower = text.lower()

    # 1. Heading check: Up to 0.40 points
    for hp in definition.heading_patterns:
        if re.search(hp, text, re.IGNORECASE):
            score += 0.40
            break

    # 2. Body regex pattern checks: Up to 0.40 points (0.20 per matching pattern, max 2)
    body_matches = 0
    for bp in definition.body_patterns:
        if re.search(bp, text, re.IGNORECASE):
            body_matches += 1
            if body_matches >= 2:
                break
    score += min(0.40, body_matches * 0.20)

    # 3. Keyword count / density: Up to 0.20 points (0.05 per keyword, max 4)
    kw_count = 0
    for kw in definition.keywords:
        if kw in text_lower:
            kw_count += 1
            if kw_count >= 4:
                break
    score += min(0.20, kw_count * 0.05)

    return min(1.0, round(score, 2))


def detect_clauses_in_chunks(
    chunks: List[Any],
) -> List[DetectedClause]:
    """
    Scans a list of document chunks (or objects with content, page_number, embedding_metadata)
    and extracts detected clauses deterministically.
    Avoids duplicating identical clauses within the same page or section.
    """
    detected: List[DetectedClause] = []
    # Track detected clause signatures: (clause_type, page_number or paragraph)
    seen_signatures = set()

    for chunk in chunks:
        content = getattr(chunk, "content", "") if hasattr(chunk, "content") else str(chunk)
        page_num = getattr(chunk, "page_number", None)
        meta = getattr(chunk, "embedding_metadata", {}) or {}

        # Split chunk into paragraph-level segments to avoid classifying the entire document
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if len(p.strip()) > 20]
        if not paragraphs:
            paragraphs = [content.strip()] if len(content.strip()) > 20 else []

        for p_idx, para in enumerate(paragraphs):
            for cdef in CLAUSE_DEFINITIONS:
                match_score = score_text_for_clause(para, cdef)
                if match_score >= cdef.min_score:
                    # Construct signature
                    sig_ref = page_num if page_num is not None else meta.get("paragraph_index", p_idx)
                    sig = (cdef.clause_type, sig_ref)
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        detected.append(
                            DetectedClause(
                                clause_type=cdef.clause_type,
                                title=cdef.title,
                                text=para,
                                page_number=page_num,
                                rule_match_indicator=match_score,
                                metadata={
                                    "paragraph_index": p_idx,
                                    "chunk_index": getattr(chunk, "chunk_index", None),
                                    **meta,
                                },
                            )
                        )

    return detected
