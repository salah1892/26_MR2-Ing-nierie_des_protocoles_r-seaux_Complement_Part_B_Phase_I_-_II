from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    action: str  # allow | refuse | escalate
    reason: str


_SENSITIVE_PATTERNS = [
    # Tunisian CIN is often 8 digits; keep it conservative to reduce false positives.
    ("cin_like", re.compile(r"\b\d{8}\b")),
    ("phone_like", re.compile(r"\b(\+?216)?\s?\d{2}\s?\d{3}\s?\d{3}\b")),
    ("email_like", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
]


def check_safety(user_text: str) -> SafetyDecision:
    text = user_text.strip()
    for name, pat in _SENSITIVE_PATTERNS:
        if pat.search(text):
            return SafetyDecision(
                action="refuse",
                reason=f"Detected sensitive citizen-identifiable data ({name}).",
            )

    # Add a light escalation trigger for complaints/threats.
    if any(w in text.lower() for w in ["plainte", "réclamation", "tribunal", "menace"]):
        return SafetyDecision(action="escalate", reason="User requests legal/complaint handling.")

    return SafetyDecision(action="allow", reason="No sensitive data detected.")
