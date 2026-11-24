"""
LexFlow AI - Deterministic Contract Obligation & Deadline Extraction Service.

Extracts actionable contractual obligations, responsible parties, and deadlines
using modal verb syntax, regex date parsers, and recurrence patterns.
Does NOT fabricate or hallucinate calendar dates from relative timeframes.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import re

from app.models.enums import ObligationFrequency, ObligationStatus
from app.services.clause_detector import DetectedClause


@dataclass
class ExtractedObligation:
    """Represents an extracted contractual obligation ready for persistence."""

    title: str
    description: str
    responsible_party: str
    due_date: Optional[date]
    frequency: str
    status: str = ObligationStatus.PENDING.value
    clause_index: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


# Known Party Roles
KNOWN_PARTIES = [
    r"\bvendor\b",
    r"\bclient\b",
    r"\bcustomer\b",
    r"\bcontractor\b",
    r"\bcompany\b",
    r"\bconsultant\b",
    r"\bservice\s+provider\b",
    r"\blicensor\b",
    r"\blicensee\b",
    r"\brecipient\b",
    r"\bdisclosing\s+party\b",
    r"\breceiving\s+party\b",
    r"\beach\s+party\b",
    r"\bboth\s+parties\b",
    r"\neither\s+party\b",
    r"\buser\b",
    r"\bdeveloper\b",
    r"\bemployer\b",
    r"\bemployee\b",
]

# Modal Verb Obligation Trigger Regex Pattern
MODAL_TRIGGER_PATTERN = re.compile(
    r"\b(?:shall(?:\s+be)?|must(?:\s+be)?|agrees?\s+to|is\s+required\s+to|are\s+required\s+to|"
    r"will\s+be\s+responsible\s+for|undertakes?\s+to|covenants?\s+to|obligated\s+to)\b",
    re.IGNORECASE,
)

# Actionable Verbs following modal verbs or defining duties
ACTIONABLE_VERBS = (
    r"\b(?:pay|paid|payment|provide|provided|deliver|delivered|perform|performed|maintain|notify|notified|"
    r"submit|submitted|furnish|execute|comply|return|destroy|protect|defend|indemnify|reimburse|issue|"
    r"implement|complete|report|audit|cooperate|warrant|remit)\b"
)

# Modal Verb Obligation Patterns
MODAL_PATTERNS = [
    re.compile(
        rf"(?P<party>[A-Z][A-Za-z0-9\s\-]+?)\s+(?:shall|must|is\s+required\s+to|agrees\s+to|undertakes\s+to|covenants\s+to|will\s+be\s+responsible\s+for)\s+(?P<action>{ACTIONABLE_VERBS}\b[^.;:\n]+)",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:shall|must|is\s+required\s+to|agrees\s+to|undertakes\s+to)\s+(?P<action>{ACTIONABLE_VERBS}\b[^.;:\n]+)",
        re.IGNORECASE,
    ),
]

# Month Name Mapping
MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# Regex for exact calendar dates
DATE_PATTERNS = [
    # YYYY-MM-DD
    re.compile(r"\b(?P<year>20\d\d)[-/](?P<month>0?[1-9]|1[0-2])[-/](?P<day>0?[1-9]|[12]\d|3[01])\b"),
    # DD/MM/YYYY or DD-MM-YYYY
    re.compile(r"\b(?P<day>0?[1-9]|[12]\d|3[01])[-/](?P<month>0?[1-9]|1[0-2])[-/](?P<year>20\d\d)\b"),
    # Month Day, Year (e.g., January 15, 2026 or Jan 15, 2026)
    re.compile(
        r"\b(?P<month_name>january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(?P<year>20\d\d)\b",
        re.IGNORECASE,
    ),
    # Day of Month Year (e.g., 15th day of March, 2026)
    re.compile(
        r"\b(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?(?P<month_name>january|february|march|april|may|june|july|august|september|october|november|december)\s*,?\s+(?P<year>20\d\d)\b",
        re.IGNORECASE,
    ),
]

# Relative deadline patterns
RELATIVE_DEADLINE_PATTERNS = [
    re.compile(r"\b(?:within|no\s+later\s+than)\s+\d+\s+(?:calendar\s+|business\s+)?days\b", re.IGNORECASE),
    re.compile(r"\bnet\s+(?:15|30|45|60|90)\b", re.IGNORECASE),
    re.compile(r"\bwithin\s+(?:one|two|three|five|ten|thirty|sixty|ninety)\s+(?:\(\d+\)\s+)?(?:calendar\s+|business\s+)?days\b", re.IGNORECASE),
    re.compile(r"\bwithin\s+\d+\s+(?:months|weeks|hours)\b", re.IGNORECASE),
    re.compile(r"\bprior\s+to\s+(?:the\s+)?(?:effective\s+date|expiration|commencement)\b", re.IGNORECASE),
    re.compile(r"\bupon\s+(?:written\s+)?(?:notice|request|receipt|delivery|invoice)\b", re.IGNORECASE),
]

# Recurrence patterns
RECURRENCE_PATTERNS = [
    (re.compile(r"\b(?:monthly|each\s+month|per\s+month|first\s+day\s+of\s+each\s+month)\b", re.IGNORECASE), ObligationFrequency.RECURRING_MONTHLY.value),
    (re.compile(r"\b(?:quarterly|each\s+quarter|per\s+quarter)\b", re.IGNORECASE), ObligationFrequency.RECURRING_QUARTERLY.value),
    (re.compile(r"\b(?:annually|each\s+year|per\s+year|annual|yearly)\b", re.IGNORECASE), ObligationFrequency.RECURRING_ANNUAL.value),
    (re.compile(r"\b(?:as\s+needed|upon\s+request|from\s+time\s+to\s+time)\b", re.IGNORECASE), ObligationFrequency.AS_NEEDED.value),
]


def parse_calendar_date(text: str) -> Optional[date]:
    """
    Deterministically parses an explicit calendar date from text.
    Returns None if no full calendar date is present (will NOT invent or hallucinate dates).
    """
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            groups = match.groupdict()
            try:
                year = int(groups["year"])
                if "month_name" in groups and groups["month_name"]:
                    month = MONTHS.get(groups["month_name"].lower(), 1)
                else:
                    month = int(groups["month"])
                day = int(groups["day"])
                return date(year, month, day)
            except (ValueError, KeyError):
                continue
    return None


def extract_relative_deadline(text: str) -> Optional[str]:
    """Extracts relative deadline phrases (e.g., 'within 30 days', 'net 30')."""
    for pattern in RELATIVE_DEADLINE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0).strip()
    return None


def detect_frequency(text: str) -> str:
    """Detects recurring frequency from obligation text."""
    for pattern, freq in RECURRENCE_PATTERNS:
        if pattern.search(text):
            return freq
    return ObligationFrequency.ONE_TIME.value


def identify_responsible_party(sentence: str) -> str:
    """
    Identifies responsible party in the sentence, prioritizing known roles.
    Defaults to 'Unspecified (Needs Review)' if party is ambiguous or unstated.
    """
    for party_pattern in KNOWN_PARTIES:
        match = re.search(party_pattern, sentence, re.IGNORECASE)
        if match:
            return match.group(0).strip().title()

    # Look for capitalized Subject preceding 'shall' or 'must'
    match = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:shall|must|agrees\s+to)\b", sentence)
    if match:
        candidate = match.group(1).strip()
        if candidate.lower() not in ("this", "the", "that", "it", "section", "clause", "article"):
            return candidate

    return "Unspecified (Needs Review)"


def split_into_sentences(text: str) -> List[str]:
    """Splits text into cleaned sentences, handling abbreviations safely."""
    # Replace common abbreviations temporarily
    cleaned = text.replace("e.g.", "eg").replace("i.e.", "ie").replace("etc.", "etc")
    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [s.strip() for s in raw_sentences if len(s.strip()) > 15]


def extract_obligations_from_clauses(
    detected_clauses: List[DetectedClause],
    raw_chunks: List[Any],
) -> List[ExtractedObligation]:
    """
    Scans detected clauses and raw chunks to extract actionable contractual obligations.
    Associates obligations with detected clause indices where applicable.
    """
    obligations: List[ExtractedObligation] = []
    seen_descriptions = set()

    # 1. Extract from detected clauses
    for c_idx, clause in enumerate(detected_clauses):
        sentences = split_into_sentences(clause.text)
        for sentence in sentences:
            # Check if sentence contains modal triggers
            if not MODAL_TRIGGER_PATTERN.search(sentence):
                continue

            # Check if sentence has actionable verb
            if not re.search(ACTIONABLE_VERBS, sentence, re.IGNORECASE):
                continue

            # Deduplication
            desc_key = sentence[:80].lower()
            if desc_key in seen_descriptions:
                continue
            seen_descriptions.add(desc_key)

            party = identify_responsible_party(sentence)
            exact_date = parse_calendar_date(sentence)
            relative_deadline = extract_relative_deadline(sentence)
            frequency = detect_frequency(sentence)

            # Generate descriptive title
            title_prefix = f"[{party}]" if party != "Unspecified (Needs Review)" else "[Action Required]"
            action_summary = sentence[:60].strip()
            if len(sentence) > 60:
                action_summary += "..."
            title = f"{title_prefix} {action_summary}"

            # Append relative deadline note to description if present
            full_description = sentence
            if relative_deadline and not exact_date:
                full_description += f"\n\n[Deadline Note: Relative timeframe '{relative_deadline}' detected. Exact date requires trigger event reference.]"

            obligations.append(
                ExtractedObligation(
                    title=title,
                    description=full_description,
                    responsible_party=party,
                    due_date=exact_date,
                    frequency=frequency,
                    status=ObligationStatus.PENDING.value,
                    clause_index=c_idx,
                    metadata={
                        "relative_deadline": relative_deadline,
                        "clause_type": clause.clause_type,
                    },
                )
            )

    # 2. Extract from raw chunks for any unclassified sections
    for chunk in raw_chunks:
        content = getattr(chunk, "content", "") if hasattr(chunk, "content") else str(chunk)
        sentences = split_into_sentences(content)
        for sentence in sentences:
            if not MODAL_TRIGGER_PATTERN.search(sentence):
                continue
            if not re.search(ACTIONABLE_VERBS, sentence, re.IGNORECASE):
                continue

            desc_key = sentence[:80].lower()
            if desc_key in seen_descriptions:
                continue
            seen_descriptions.add(desc_key)

            party = identify_responsible_party(sentence)
            exact_date = parse_calendar_date(sentence)
            relative_deadline = extract_relative_deadline(sentence)
            frequency = detect_frequency(sentence)

            title_prefix = f"[{party}]" if party != "Unspecified (Needs Review)" else "[Action Required]"
            action_summary = sentence[:60].strip()
            if len(sentence) > 60:
                action_summary += "..."
            title = f"{title_prefix} {action_summary}"

            full_description = sentence
            if relative_deadline and not exact_date:
                full_description += f"\n\n[Deadline Note: Relative timeframe '{relative_deadline}' detected. Exact date requires trigger event reference.]"

            obligations.append(
                ExtractedObligation(
                    title=title,
                    description=full_description,
                    responsible_party=party,
                    due_date=exact_date,
                    frequency=frequency,
                    status=ObligationStatus.PENDING.value,
                    clause_index=None,
                    metadata={"relative_deadline": relative_deadline},
                )
            )

    return obligations
