"""Input guardrails and lightweight language detection."""

from __future__ import annotations

import re
from typing import Tuple


_BLOCK_PATTERNS = [
    r"<\s*script",
    r"ignore\s+(all\s+)?(previous|prior|above)\s*(instructions|prompts?|rules?|directions?)?",
    r"disregard\s+(all\s+)?(prior|previous|above)",
    r"reveal\s+(your|the|my)?\s*(system\s*)?prompt",
    r"show\s+(me\s+)?(your|the)\s+(system|hidden|secret)\s+(prompt|instructions?)",
    r"jailbreak",
    r"prompt\s*injection",
    r"drop\s+table",
    r"select\s+\*\s+from",
    r";\s*--",
    r"union\s+select",
    r"<\|.*?\|>",
]

_BLOCK_RE = re.compile("|".join(_BLOCK_PATTERNS), re.IGNORECASE)


_HI_RE = re.compile(r"[\u0900-\u097F]")


def validate_input(text: str) -> Tuple[bool, str]:
    """Return (is_valid, message). ``message`` is the rejection reason when invalid."""
    if not isinstance(text, str):
        return False, "Invalid input type."

    cleaned = text.strip()
    if not cleaned:
        return False, "Please type a question or message."
    if len(cleaned) > 2000:
        return False, "Your message is too long. Please shorten it."
    if _BLOCK_RE.search(cleaned):
        return False, "I can't help with that request for safety reasons."

    return True, ""


def detect_language(text: str) -> str:
    """Return ``"hi"`` if Devanagari characters dominate, else ``"en"``."""
    if not text:
        return "en"
    devanagari = len(_HI_RE.findall(text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if devanagari == 0 and latin == 0:
        return "en"
    return "hi" if devanagari > latin else "en"
