"""Centralized medical safety disclaimer.

A disclaimer is a necessary (though not sufficient) safety control for any
AI-generated health information. `ensure_disclaimer` guarantees *every* agent
response carries one, without double-appending when an agent already included
its own.
"""
from __future__ import annotations

MEDICAL_DISCLAIMER = (
    "\n\n---\n"
    "⚕️ **Important:** This is AI-generated information for educational purposes only. "
    "It is **not** a medical diagnosis and is not a substitute for professional medical "
    "advice. Always consult a qualified healthcare provider about your health, and call "
    "your local emergency number for urgent or life-threatening symptoms."
)

# Substrings that indicate a disclaimer is already present (case-insensitive).
# Models phrase it variably ("not a substitute for a professional medical
# evaluation"), so match the stable core phrase rather than an exact string.
_MARKERS = ("not a substitute for", "consult a qualified healthcare", "not a medical diagnosis")


def ensure_disclaimer(text: str | None) -> str:
    body = text or ""
    low = body.lower()
    if any(m in low for m in _MARKERS):
        return body
    return body + MEDICAL_DISCLAIMER
