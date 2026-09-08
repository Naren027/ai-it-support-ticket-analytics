import requests
import json
import re


# ============================================================
# AI CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

REQUEST_TIMEOUT = 180


# ============================================================
# FINAL IT TRIAGE RUBRIC
# ============================================================

SYSTEM_INSTRUCTIONS = """
You are an experienced IT service desk triage analyst.

Your job is to classify an IT support ticket using ONLY the
information contained in the ticket.

The ticket text may be noisy, repetitive, incomplete, or contain
email fragments. Do not assume information that is not stated.

============================================================
STEP 1 — EXTRACT OPERATIONAL EVIDENCE
============================================================

Determine whether the ticket contains evidence for each item:

work_blocked:
true if the user explicitly cannot work, cannot perform a required
task, is blocked, or functionality prevents required work.

deadline_present:
true if a specific deadline, date, meeting, launch, onboarding,
delivery, or time requirement is stated.

explicit_urgency:
true if the ticket explicitly indicates urgent, ASAP, immediate,
high importance, emergency, or similar urgency.

service_unavailable:
true if a system, application, server, website, network, or service
is explicitly unavailable or not working.

security_issue:
true if the ticket concerns a security incident, compromised
account, suspicious activity, unauthorized access, malware,
phishing, or another security event.

multiple_users:
true only when the ticket explicitly indicates multiple users,
a team, department, widespread users, or organization-wide impact.

business_critical:
true if the ticket explicitly affects a critical business process,
production operation, major operational activity, or significant
business service.

limited_functionality:
true if something is partially working, only one component/system
remains functional, or functionality is significantly reduced.

============================================================
STEP 2 — PRIORITY
============================================================

LOW:
Routine request or minor issue with no significant work impact.

Examples:
- Account creation
- Routine access request
- Normal equipment request
- Administrative request
- Purchase request
- General configuration
- Information request

MEDIUM:
Meaningful impact to an individual or important task, OR a clear
deadline/upcoming requirement, but no evidence of major widespread
business disruption.

Examples:
- User cannot complete an important task
- Hardware problem affecting productivity
- Access required for an upcoming activity
- Important task has a deadline
- Significant functionality is reduced
- One important process is affected

CRITICAL:
Use ONLY when there is strong evidence of severe operational impact.

Examples:
- Major production outage
- Critical business service unavailable
- Security incident
- Widespread service failure
- Multiple users significantly affected
- Critical business process stopped

IMPORTANT:
Do NOT classify a ticket as Critical simply because it contains
"urgent", "ASAP", "important", or "high priority".

Do NOT infer multiple users, production impact, or a security incident
unless the ticket explicitly supports it.

============================================================
STEP 3 — URGENCY SCORE
============================================================

Start from the evidence, not from keywords.

0-20:
Routine request with no meaningful operational impact.

21-40:
Minor issue or request with limited impact.

41-60:
Clear individual work impact, upcoming requirement, or meaningful
operational inconvenience.

61-79:
Strong evidence of blocked work, significant functionality loss,
an approaching deadline, or a task requiring prompt attention.

80-100:
Severe operational impact such as major outage, security incident,
widespread failure, or critical business process interruption.

Use the full range when justified.

Examples:

Routine account creation:
Low / approximately 0-20

Individual work problem:
Medium / approximately 45-65

Individual work blocked with a near deadline:
Medium / approximately 60-75

Major production outage affecting many users:
Critical / approximately 85-100

Security incident:
Critical / approximately 85-100

============================================================
IMPORTANT SCORING RULES
============================================================

The following evidence can increase urgency:

- work is explicitly blocked
- user cannot perform required work
- explicit deadline
- deadline is near
- service is unavailable
- significant functionality is lost
- multiple users are affected
- critical business process is affected
- security incident

However:

"urgent" alone does NOT automatically mean Critical.

A routine request containing "urgent" can still be Low or Medium.

Likewise, a technical problem should not automatically be Medium
or Critical unless its operational impact is supported by the text.

============================================================
PRIORITY VS URGENCY
============================================================

Priority and urgency are NOT identical.

Example:

A single employee has an important task blocked until tomorrow:

priority = Medium
urgency_score = 70

A routine account creation request marked "urgent":

priority = Low or Medium depending on the context
urgency_score = approximately 20-50

A production outage affecting many users:

priority = Critical
urgency_score = 90+

============================================================
NOISE HANDLING
============================================================

The ticket may contain:

- duplicated phrases
- email signatures
- greetings
- dates
- names
- repeated words
- irrelevant historical email content

Ignore those unless they provide operational evidence.

Pay attention to phrases describing:

- inability to work
- deadlines
- unavailable services
- reduced functionality
- affected users
- business impact
- security
- required dates

Do not mistake category words such as "Hardware", "Oracle",
"Confluence", "phone", "server", or "access" for severity.

============================================================
FEW-SHOT EXAMPLES
============================================================

Example 1:

Ticket:
"please create a confluence account for me thank you"

Classification:
Low / 10

Reason:
Routine access request with no stated operational impact.

Example 2:

Ticket:
"my laptop screen is not working and I cannot continue my work"

Classification:
Medium / 65

Reason:
The hardware problem is explicitly preventing the user from working.

Example 3:

Ticket:
"urgent request, need access before tomorrow's meeting"

Classification:
Medium / 65

Reason:
The request has explicit urgency and a near-term deadline.

Example 4:

Ticket:
"production server is down and multiple users cannot access the
application"

Classification:
Critical / 95

Reason:
A production service outage is affecting multiple users.

Example 5:

Ticket:
"please order a new monitor when possible"

Classification:
Low / 10

Reason:
Routine equipment request with no stated work disruption.

Example 6:

Ticket:
"only one system is working and I cannot complete the forecast,
need this done by Friday"

Classification:
Medium / 70

Reason:
The ticket indicates reduced functionality, blocked work, and a
specific deadline.

Example 7:

Ticket:
"suspicious login detected and account may be compromised"

Classification:
Critical / 95

Reason:
The ticket describes a potential security incident.

============================================================
FINAL DECISION
============================================================

Before deciding, mentally answer:

1. What is the user actually asking for?
2. Is anyone unable to work?
3. Is there a deadline?
4. Is there an unavailable service?
5. Is functionality significantly reduced?
6. Are multiple users affected?
7. Is there a security issue?
8. Is there major business impact?
9. Which evidence is strongest?

Do not invent missing information.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

Use exactly these fields:

{
  "priority": "Low",
  "urgency_score": 0,
  "urgency_reason": "Short explanation",
  "work_blocked": false,
  "deadline_present": false,
  "explicit_urgency": false,
  "service_unavailable": false,
  "security_issue": false,
  "multiple_users": false,
  "business_critical": false,
  "limited_functionality": false
}

Rules:

priority must be exactly:
Low
Medium
Critical

urgency_score must be an integer from 0 to 100.

All evidence fields must be true or false.

urgency_reason must be one concise sentence.

Do not include markdown.
Do not include additional fields.
"""


# ============================================================
# CLASSIFICATION FUNCTION
# ============================================================

def classify_ticket(ticket_text):

    if not isinstance(ticket_text, str):
        raise ValueError("Ticket text must be a string.")

    ticket_text = ticket_text.strip()

    if not ticket_text:
        raise ValueError("Ticket text is empty.")

    prompt = f"""
{SYSTEM_INSTRUCTIONS}

============================================================
TICKET TO CLASSIFY
============================================================

{ticket_text}

============================================================
RETURN JSON ONLY
============================================================
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.8
        }
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        api_result = response.json()

        model_response = api_result.get(
            "response",
            ""
        ).strip()

        if not model_response:
            raise ValueError(
                "Ollama returned an empty response."
            )

        parsed_result = json.loads(
            model_response
        )

        return parsed_result

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "Ollama request timed out."
        )

    except json.JSONDecodeError:

        raise RuntimeError(
            "Model returned invalid JSON:\n"
            + model_response
        )

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"Ollama API request failed: {error}"
        )


# ============================================================
# RESULT VALIDATION
# ============================================================

def validate_result(result):

    required_fields = [
        "priority",
        "urgency_score",
        "urgency_reason",
        "work_blocked",
        "deadline_present",
        "explicit_urgency",
        "service_unavailable",
        "security_issue",
        "multiple_users",
        "business_critical",
        "limited_functionality"
    ]

    for field in required_fields:

        if field not in result:

            raise ValueError(
                f"Missing required field: {field}"
            )

    valid_priorities = [
        "Low",
        "Medium",
        "Critical"
    ]

    if result["priority"] not in valid_priorities:

        raise ValueError(
            f"Invalid priority: "
            f"{result['priority']}"
        )

    try:

        urgency_score = int(
            result["urgency_score"]
        )

    except (ValueError, TypeError):

        raise ValueError(
            "Urgency score must be an integer."
        )

    if not 0 <= urgency_score <= 100:

        raise ValueError(
            "Urgency score must be between "
            "0 and 100."
        )

    if not isinstance(
        result["urgency_reason"],
        str
    ):

        raise ValueError(
            "Urgency reason must be text."
        )

    boolean_fields = [
        "work_blocked",
        "deadline_present",
        "explicit_urgency",
        "service_unavailable",
        "security_issue",
        "multiple_users",
        "business_critical",
        "limited_functionality"
    ]

    for field in boolean_fields:

        if not isinstance(
            result[field],
            bool
        ):

            raise ValueError(
                f"{field} must be true or false."
            )

    return True


# ============================================================
# SAFETY / CONSISTENCY NORMALIZATION
# ============================================================

def normalize_result(result):

    """
    Apply deterministic business rules after the AI response.

    The AI performs interpretation.
    Python performs consistency checks.

    This prevents obviously contradictory classifications.
    """

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if result["security_issue"]:

        if result["priority"] != "Critical":

            result["priority"] = "Critical"

        if result["urgency_score"] < 85:

            result["urgency_score"] = 85

    # --------------------------------------------------------
    # MAJOR BUSINESS / WIDESPREAD IMPACT
    # --------------------------------------------------------

    if (
        result["multiple_users"]
        and result["business_critical"]
    ):

        result["priority"] = "Critical"

        if result["urgency_score"] < 85:

            result["urgency_score"] = 85

    # --------------------------------------------------------
    # CRITICAL SERVICE FAILURE
    # --------------------------------------------------------

    if (
        result["service_unavailable"]
        and result["business_critical"]
    ):

        result["priority"] = "Critical"

        if result["urgency_score"] < 80:

            result["urgency_score"] = 80

    # --------------------------------------------------------
    # STRONG INDIVIDUAL IMPACT
    # --------------------------------------------------------

    if (
        result["work_blocked"]
        and result["deadline_present"]
    ):

        if result["priority"] == "Low":

            result["priority"] = "Medium"

        if result["urgency_score"] < 60:

            result["urgency_score"] = 60

    # --------------------------------------------------------
    # REDUCED FUNCTIONALITY + WORK IMPACT
    # --------------------------------------------------------

    if (
        result["limited_functionality"]
        and result["work_blocked"]
    ):

        if result["priority"] == "Low":

            result["priority"] = "Medium"

        if result["urgency_score"] < 55:

            result["urgency_score"] = 55

    # --------------------------------------------------------
    # EXPLICIT DEADLINE + WORK IMPACT
    # --------------------------------------------------------

    if (
        result["deadline_present"]
        and result["work_blocked"]
    ):

        if result["urgency_score"] < 60:

            result["urgency_score"] = 60

    # --------------------------------------------------------
    # PREVENT LOW + STRONG EVIDENCE CONTRADICTION
    # --------------------------------------------------------

    strong_evidence = (
        result["work_blocked"]
        or result["business_critical"]
        or result["security_issue"]
        or (
            result["deadline_present"]
            and result["limited_functionality"]
        )
    )

    if (
        strong_evidence
        and result["priority"] == "Low"
    ):

        result["priority"] = "Medium"

    return result


# ============================================================
# FINAL VALIDATION AFTER NORMALIZATION
# ============================================================

def validate_normalized_result(result):

    validate_result(result)

    # Critical requires strong supporting evidence.
    critical_evidence = (
        result["security_issue"]
        or result["business_critical"]
        or (
            result["multiple_users"]
            and result["service_unavailable"]
        )
    )

    if (
        result["priority"] == "Critical"
        and not critical_evidence
    ):

        result["priority"] = "Medium"

        if result["urgency_score"] > 79:

            result["urgency_score"] = 79

    return True


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("AI IT SUPPORT TICKET CLASSIFIER - FINAL VERSION")
    print("=" * 70)

    test_ticket = (
        "oracle pas urgent re we updated rights query "
        "hi can get some assistance here looks like have "
        "full control for codes only one working for "
        "cannot forecast need done by friday thanks "
        "programme portfolio officer mobile phone"
    )

    print("\nModel:")
    print(MODEL_NAME)

    print("\nTest ticket:")
    print(test_ticket)

    print("\nSending ticket to local Ollama model...")

    result = classify_ticket(
        test_ticket
    )

    validate_result(
        result
    )

    print("\nRaw AI classification:")

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    result = normalize_result(
        result
    )

    validate_normalized_result(
        result
    )

    print("\nFinal validated classification:")

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print("\n" + "=" * 70)
    print("FINAL AI CLASSIFIER TEST COMPLETED")
    print("=" * 70)