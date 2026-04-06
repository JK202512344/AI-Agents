"""
guardrails.py

Improved Version:
- Hybrid guardrails (rule-based + semantic)
- Fixes false prompt injection (e.g., "system architecture")
- Safe query bypass (education + business)
- Strong PII masking
- Clean, production-ready structure
"""

import re
from typing import Tuple

from semantic_router import Route, SemanticRouter
from shared_encoder import get_encoder

# =========================
# ROUTES (Semantic)
# =========================

off_topic_route = Route(
    name="off_topic",
    utterances=[
        "joke", "weather", "movie", "sports score",
        "tell me something fun", "random fact", "poem", "story"
    ],
)

prompt_injection_route = Route(
    name="prompt_injection",
    utterances=[
        "ignore previous instructions",
        "ignore system instructions",
        "bypass all rules",
        "act as system",
        "reveal system prompt",
    ],
)

harmful_route = Route(
    name="harmful",
    utterances=[
        "hack account", "steal money", "fraud", "insider trading"
    ],
)

input_guardrail_router = SemanticRouter(
    encoder=get_encoder(),
    routes=[off_topic_route, prompt_injection_route, harmful_route],
    auto_sync="local",
)

# =========================
# CONFIG
# =========================

THRESHOLDS = {
    "harmful": 0.65,
    "prompt_injection": 0.85,  # 🔥 stricter to avoid false positives
    "off_topic": 0.75,
}

# Strong rule-based detection (high precision)
INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore system",
    "bypass",
    "override",
    "act as",
    "reveal prompt",
    "system prompt",
]

SAFE_TOPICS = [
    "what is",
    "explain",
    "define",
    "architecture",
    "system design",
    "engineering",
]

BUSINESS_KEYWORDS = [
    "finemp", "employee", "details", "email", "salary"
]

PII_PATTERNS = {
    "email": r"\b[\w\.-]+@[\w\.-]+\.\w+\b",
    "phone": r"\b(?:\+91[\-\s]?|0)?[6-9]\d{9}\b",
    "aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
}

# =========================
# HELPERS
# =========================

def is_prompt_injection(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in INJECTION_KEYWORDS)


def mask_email(email: str) -> str:
    try:
        local, domain = email.split("@")
        if len(local) <= 2:
            return local[0] + "*" + "@" + domain

        return (
            local[0]
            + "*" * (len(local) // 2)
            + local[-2]
            + "*"
            + local[-1]
            + "@"
            + domain
        )
    except Exception:
        return "XXXXX"


def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 4:
        return "XXXXX"

    return (
        digits[0]
        + "*" * (len(digits) // 2)
        + digits[-2]
        + "*"
        + digits[-1]
    )

# =========================
# GUARDRAILS CLASS
# =========================

class Guardrails:
    def __init__(self, max_queries: int = 200):
        self.query_count = 0
        self.max_queries = max_queries

    def reset(self):
        self.query_count = 0

    # ================= INPUT =================
    def check_input(self, query: str) -> Tuple[bool, str]:
        self.query_count += 1

        if self.query_count > self.max_queries:
            return False, "Session limit exceeded."

        q = query.lower()

        # ---- PII BLOCK ----
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, query):
                return False, f"Sensitive data detected ({pii_type})."

        # ---- HARD PROMPT INJECTION (rule-based) ----
        if is_prompt_injection(query):
            return False, "Prompt injection detected."

        # ---- SAFE EDUCATIONAL QUERIES ----
        if any(k in q for k in SAFE_TOPICS):
            return True, ""

        # ---- BUSINESS QUERY BYPASS ----
        if any(k in q for k in BUSINESS_KEYWORDS):
            return True, ""

        # ---- SEMANTIC ROUTING ----
        try:
            route = input_guardrail_router(query)

            if route:
                score = route.similarity_score
                name = route.name

                if score > THRESHOLDS.get(name, 1.0):

                    if name == "off_topic":
                        return False, "Only FinSolve-related queries are allowed."

                    if name == "prompt_injection":
                        return False, "Prompt injection detected."

                    if name == "harmful":
                        return False, "This request is not allowed."

        except Exception:
            pass

        return True, ""

    # ================= OUTPUT =================
    def check_output(self, answer: str, context: str, user_role: str):
        """
        Returns:
        (is_blocked, safe_answer)
        """

        redacted = answer

        # ---- EMAIL ----
        redacted = re.sub(
            PII_PATTERNS["email"],
            lambda m: mask_email(m.group()) if "*" not in m.group() else m.group(),
            redacted
        )

        # ---- PHONE ----
        redacted = re.sub(
            PII_PATTERNS["phone"],
            lambda m: mask_phone(m.group()) if "*" not in m.group() else m.group(),
            redacted
        )

        # ---- AADHAAR ----
        redacted = re.sub(PII_PATTERNS["aadhaar"], "XXXXXXXXXXXX", redacted)

        # ---- SALARY ----
        redacted = re.sub(
            r"(salary\s*:\s*)([\d\.]+)",
            r"\1XXXXX",
            redacted,
            flags=re.I
        )

        # ---- DOB ----
        redacted = re.sub(
            r"(date_of_birth\s*:\s*)([\d\-]+)",
            r"\1XXXXX",
            redacted,
            flags=re.I
        )

        return False, redacted