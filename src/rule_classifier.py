import re

from ai_classifier import (
    normalize_result,
    validate_normalized_result
)


# ============================================================
# PURPOSE
# ============================================================
#
# This module tries to classify a ticket WITHOUT calling the LLM,
# but only when the evidence is unambiguous.
#
# It reuses ai_classifier.normalize_result() and
# ai_classifier.validate_normalized_result() unchanged, so any
# ticket classified here follows the exact same business rules
# as an LLM-classified ticket.
#
# If the rule pass is not confident, classify_with_rules() returns
# None, and the caller should fall back to the LLM classifier.
#
# ============================================================


# ============================================================
# NEGATION GUARD
# ============================================================

NEGATION_WINDOW = 4  # words before the match to check for negation

NEGATION_WORDS = {
    "not", "no", "never", "n't", "without", "isn't", "wasn't",
    "cannot", "don't", "didn't", "cancel", "cancelled", "resolved"
}


def _is_negated(text, match_start):
    """
    Very simple negation check: looks at the few words immediately
    before a keyword match. If a negation word is present, we treat
    the match as unreliable and skip it, rather than risk asserting
    a flag that isn't actually true.
    """

    preceding_text = text[:match_start]
    words = preceding_text.split()[-NEGATION_WINDOW:]

    return any(
        word.strip(".,!?").lower() in NEGATION_WORDS
        for word in words
    )


# ============================================================
# FLAG PATTERNS
# ============================================================
#
# Patterns are drawn directly from the definitions and few-shot
# examples in ai_classifier.SYSTEM_INSTRUCTIONS, to keep the two
# classifiers aligned in intent.
#
# ============================================================

FLAG_PATTERNS = {

    "security_issue": [
        r"\bcompromis(ed|e)\b",
        r"\bphishing\b",
        r"\bmalware\b",
        r"\bransomware\b",
        r"\bunauthoriz(ed|ation)\b",
        r"\bsuspicious (login|activity|access)\b",
        r"\bhack(ed|ing)?\b",
        r"\bsecurity (incident|breach|issue)\b",
        r"\bdata breach\b",
        r"\bvirus\b",
    ],

    "service_unavailable": [
        r"\b(is|are|was)\s+down\b",
        r"\bnot\s+working\b",
        r"\bcannot\s+access\b",
        r"\bcan't\s+access\b",
        r"\bunavailable\b",
        r"\boutage\b",
        r"\bnot\s+responding\b",
        r"\bcrash(ed|ing)?\b",
        r"\boffline\b",
        r"\bserver\s+(is\s+)?down\b",
    ],

    "business_critical": [
        r"\bproduction\s+(server|system|environment|down|outage)\b",
        r"\bbusiness[\s-]critical\b",
        r"\bcritical\s+(business|process|system|service)\b",
        r"\bmajor\s+operational\b",
    ],

    "multiple_users": [
        r"\bmultiple\s+users\b",
        r"\ball\s+users\b",
        r"\bentire\s+team\b",
        r"\bwhole\s+department\b",
        r"\borganization[\s-]wide\b",
        r"\bcompany[\s-]wide\b",
        r"\bseveral\s+(employees|users|people)\b",
        r"\beveryone\s+(is|can't|cannot)\b",
    ],

    "work_blocked": [
        r"\bcannot\s+(work|continue|complete|perform)\b",
        r"\bcan't\s+(work|continue|complete|perform)\b",
        r"\bunable\s+to\s+(work|continue|complete|perform)\b",
        r"\bblocked\b",
        r"\bprevent(s|ing)?\s+me\s+from\s+working\b",
        r"\bstuck\s+and\s+cannot\b",
    ],

    "deadline_present": [
        r"\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bby\s+tomorrow\b",
        r"\bbefore\s+tomorrow\b",
        r"\bdue\s+(date|by|on)?\b",
        r"\bdeadline\b",
        r"\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b",
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}\b",
        r"\bmeeting\s+(on|at|tomorrow|today)\b",
    ],

    "explicit_urgency": [
        r"\burgent\b",
        r"\basap\b",
        r"\bimmediately\b",
        r"\bemergency\b",
        r"\bhigh\s+priority\b",
        r"\bas\s+soon\s+as\s+possible\b",
    ],

    "limited_functionality": [
        r"\bonly\s+one\s+(system|application|component)\b",
        r"\bpartially\s+working\b",
        r"\breduced\s+functionality\b",
        r"\bnot\s+fully\s+working\b",
        r"\bpartial\s+outage\b",
        r"\bsome\s+features?\s+(not|aren't|are\s+not)\s+working\b",
    ],
}


# ============================================================
# ROUTINE / LOW SIGNALS
# ============================================================
#
# Used only to positively confirm an "obviously Low" ticket -
# short, routine, no evidence flags triggered.
#
# ============================================================

ROUTINE_PATTERNS = [
    r"\bplease\s+(create|order|set\s?up|provide)\b",
    r"\brequest(ing)?\s+(access|account|new)\b",
    r"\bwhen\s+possible\b",
    r"\bcould\s+you\s+please\b",
]

MAX_ROUTINE_LENGTH_WORDS = 40


# ============================================================
# FLAG EXTRACTION
# ============================================================

def extract_flags(text):
    """
    Returns a dict of {flag_name: bool} based on keyword matches,
    with a simple negation guard applied.
    """

    flags = {}

    for flag_name, patterns in FLAG_PATTERNS.items():

        matched = False

        for pattern in patterns:

            for match in re.finditer(pattern, text, re.IGNORECASE):

                if not _is_negated(text, match.start()):

                    matched = True
                    break

            if matched:
                break

        flags[flag_name] = matched

    return flags


# ============================================================
# CONFIDENCE DECISION
# ============================================================

def _is_confident_low(text, flags):

    if any(flags.values()):
        return False

    word_count = len(text.split())

    if word_count > MAX_ROUTINE_LENGTH_WORDS:
        return False

    for pattern in ROUTINE_PATTERNS:

        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def _is_confident_security(flags):

    # normalize_result() forces Critical/85+ whenever security_issue
    # is true, regardless of other flags - so a clean security match
    # alone is safe to commit to.
    return flags["security_issue"]


def _is_confident_outage(flags):

    # normalize_result() forces Critical when service_unavailable
    # and business_critical are both true - safe to commit to.
    # Also covers the "multiple_users + service_unavailable" critical
    # check inside validate_normalized_result().
    return (
        flags["service_unavailable"]
        and (flags["business_critical"] or flags["multiple_users"])
    )


# ============================================================
# BASELINE PRIORITY / URGENCY BEFORE NORMALIZATION
# ============================================================
#
# These starting values intentionally mirror the low end of each
# rubric band. normalize_result() then applies the same upward
# adjustments it applies to LLM output, so confident rule-based
# tickets converge to the same final numbers an LLM would produce
# for equally unambiguous evidence.
#
# ============================================================

def _baseline_result(flags):

    priority = "Low"
    urgency_score = 10

    if flags["work_blocked"]:
        priority = "Medium"
        urgency_score = max(urgency_score, 50)

    if flags["limited_functionality"]:
        urgency_score = max(urgency_score, 40)

    if flags["deadline_present"]:
        urgency_score = max(urgency_score, 45)

    if flags["explicit_urgency"]:
        urgency_score = max(urgency_score, 30)

    if flags["service_unavailable"]:
        if priority == "Low":
            priority = "Medium"
        urgency_score = max(urgency_score, 60)

    if flags["multiple_users"]:
        urgency_score = max(urgency_score, 60)

    if flags["business_critical"]:
        if priority == "Low":
            priority = "Medium"
        urgency_score = max(urgency_score, 65)

    if flags["security_issue"]:
        priority = "Critical"
        urgency_score = max(urgency_score, 85)

    result = {
        "priority": priority,
        "urgency_score": urgency_score,
        "urgency_reason": "Rule-based classification from keyword evidence.",
        **flags
    }

    return result


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================

def classify_with_rules(ticket_text):
    """
    Attempts a deterministic classification.

    Returns:
        (result_dict, reason_string)  if confident
        (None, reason_string)          if not confident -> caller
                                        should fall back to the LLM

    result_dict is already passed through normalize_result() and
    validate_normalized_result(), matching the LLM code path.
    """

    if not isinstance(ticket_text, str) or not ticket_text.strip():
        return None, "empty_text"

    text = ticket_text.strip()

    flags = extract_flags(text)

    if _is_confident_low(text, flags):

        result = _baseline_result(flags)
        result["urgency_reason"] = (
            "Routine request with no operational evidence detected."
        )

        result = normalize_result(result)
        validate_normalized_result(result)

        return result, "confident_low"

    if _is_confident_security(flags):

        result = _baseline_result(flags)
        result["urgency_reason"] = (
            "Security-related keywords detected in ticket text."
        )

        result = normalize_result(result)
        validate_normalized_result(result)

        return result, "confident_security"

    if _is_confident_outage(flags):

        result = _baseline_result(flags)
        result["urgency_reason"] = (
            "Service outage combined with critical/widespread impact "
            "keywords detected."
        )

        result = normalize_result(result)
        validate_normalized_result(result)

        return result, "confident_outage"

    return None, "ambiguous"


# ============================================================
# RULES-ONLY ENTRY POINT (no LLM fallback)
# ============================================================
#
# Used by the standalone rules-only pipeline. Unlike
# classify_with_rules(), this ALWAYS returns a result - even for
# ambiguous tickets, it makes a best-effort decision from whatever
# evidence flags were detected (which may be none, resulting in a
# default Low/10).
#
# This trades some accuracy on genuinely ambiguous tickets for
# speed: no LLM call is ever made.
#
# ============================================================

def classify_ticket_rules_only(ticket_text):
    """
    Always returns a classification dict, based purely on keyword
    evidence - no LLM involved, ever.

    Raises ValueError for empty/invalid text, matching the LLM
    classifier's behavior for the same case (so the calling
    pipeline's empty-text handling still works unchanged).
    """

    if not isinstance(ticket_text, str) or not ticket_text.strip():
        raise ValueError("Ticket text is empty.")

    text = ticket_text.strip()

    flags = extract_flags(text)

    result = _baseline_result(flags)

    matched_flags = [
        name for name, value in flags.items() if value
    ]

    if matched_flags:
        result["urgency_reason"] = (
            "Rule-based decision from detected evidence: "
            + ", ".join(matched_flags) + "."
        )
    else:
        result["urgency_reason"] = (
            "No operational evidence keywords detected; "
            "treated as routine."
        )

    result = normalize_result(result)
    validate_normalized_result(result)

    return result