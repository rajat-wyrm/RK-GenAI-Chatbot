"""
fallback.py — Always-on response generator.

Produces a coherent, source-cited answer from the RAG-retrieved context alone
— no LLM required. Ensures the chatbot NEVER returns an empty or error
response, even with zero LLM keys or all providers down.

The generated response is intentionally concise, structured, and grounded
exclusively in the retrieved knowledge base.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

logger = logging.getLogger("skillnova.fallback")

# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------
_INTENT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("contact",  re.compile(r"\b(contact|reach|email|phone|call|connect|linkedin|github|portfolio)\b", re.I)),
    ("skills",   re.compile(r"\b(skill|stack|technology|technologies|language|framework|tool|expert|proficien)\b", re.I)),
    ("projects", re.compile(r"\b(project|built|build|app|application|platform|system|product)\b", re.I)),
    ("experience", re.compile(r"\b(experience|work|job|role|position|company|uptoskills|intern|employ)\b", re.I)),
    ("education", re.compile(r"\b(education|college|university|degree|study|studied|svce|chennai|aicte|pmsss|scholar)\b", re.I)),
    ("certifications", re.compile(r"\b(certific|certification|course|google cloud|jpmorgan|virtual experience)\b", re.I)),
    ("leadership", re.compile(r"\b(leadership|ncc|cadet|air wing|promotion|team|coordinate|600|interns)\b", re.I)),
    ("list",     re.compile(r"^(list|show|give me|tell me (all|the)|what are|which)\b", re.I)),
    ("how",      re.compile(r"\b(how|steps|process|guide|tutorial|way to)\b", re.I)),
    ("what",     re.compile(r"\b(what|define|meaning|explain|describe)\b", re.I)),
]


def detect_intent(question: str) -> str:
    """Return the most likely intent for ``question``."""
    q = question.strip()
    for intent, pat in _INTENT_PATTERNS:
        if pat.search(q):
            return intent
    return "general"


# ---------------------------------------------------------------------------
# Greeting / out-of-scope handling
# ---------------------------------------------------------------------------
_GREETING_RE = re.compile(r"^(hi|hello|hey|yo|sup|good (morning|afternoon|evening)|greetings)\b", re.I)


def is_greeting(text: str) -> bool:
    return bool(_GREETING_RE.match(text.strip()))


GREETING_REPLIES = [
    "Hi! I'm Rajat's personal AI assistant. Ask me about his skills, projects (InternOps, Apogee, AI Compliance Copilot), experience at UptoSkills, NCC leadership, or how to reach him.",
    "Hello! I can tell you about Rajat's background, technical skills, projects, certifications, and leadership experience. What would you like to know?",
    "Hey there! I'm here to answer questions about Rajat Kumar — his work, skills, and projects. What can I help you with?",
]


# ---------------------------------------------------------------------------
# Response shaping
# ---------------------------------------------------------------------------
def _truncate(text: str, max_chars: int = 600) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    # try to end on a sentence boundary
    for sep in [". ", "! ", "? ", "\n"]:
        idx = cut.rfind(sep)
        if idx > max_chars * 0.6:
            return cut[: idx + 1].strip()
    return cut.rstrip() + "…"


def _extract_bullets(text: str, max_items: int = 8) -> List[str]:
    """Pull a short, relevant bullet list out of a chunk of text."""
    bullets: list[str] = []
    # numbered list items
    for m in re.finditer(r"(?:^|\n)\s*(?:[-*•]|\d+[.)])\s+([^\n]{8,180})", text):
        b = m.group(1).strip()
        if b and b not in bullets:
            bullets.append(b)
        if len(bullets) >= max_items:
            break
    if bullets:
        return bullets
    # comma-separated skills
    if "," in text and len(text) < 400:
        parts = [p.strip(" .;:") for p in text.split(",") if 2 < len(p.strip()) < 60]
        return parts[:max_items]
    # single line fallback
    return [text.strip()[:200]]


def _contact_block() -> str:
    return (
        "**How to reach Rajat**\n\n"
        "- **Email:** rajatkumar7861813@gmail.com\n"
        "- **Phone:** +91 8899994263\n"
        "- **LinkedIn:** linkedin.com/in/rajat-kumar-sde\n"
        "- **GitHub:** github.com/rajat-wyrm\n"
        "- **Portfolio:** rajatkumar-portfolio.vercel.app\n"
        "- **Location:** Chennai, Tamil Nadu, India"
    )


def _format_intent_response(intent: str, question: str, docs: list) -> tuple[str, List[str]]:
    """Build a response tailored to the detected intent."""
    sources: list[str] = []
    seen: set[str] = set()

    def add_source(s: Optional[str]):
        if s and s not in seen:
            seen.add(s)
            sources.append(s)

    if intent == "contact":
        return _contact_block(), ["contact.md"]

    if not docs:
        return (
            "I don't have a confident answer in Rajat's knowledge base for that. "
            "Try asking about his skills, projects, experience, education, "
            "certifications, leadership, or contact details.",
            [],
        )

    # Collect the best doc per source
    primary = docs[0]
    add_source(primary.metadata.get("source"))

    if intent == "list":
        bullets = _extract_bullets(primary.page_content)
        body = "Here's what I found:\n\n" + "\n".join(f"- {b}" for b in bullets)
    elif intent in ("what", "how", "general"):
        body = _truncate(primary.page_content, 700)
    else:
        # skills / projects / experience / education / certifications / leadership
        body = _truncate(primary.page_content, 700)

    # Add a second source if it adds value
    if len(docs) > 1:
        second = docs[1]
        body += "\n\n" + _truncate(second.page_content, 300)
        add_source(second.metadata.get("source"))

    return body, sources


# ---------------------------------------------------------------------------
# Off-topic response
# ---------------------------------------------------------------------------
def _off_topic_response() -> dict:
    return {
        "reply": (
            "That's outside my knowledge base — I focus on Rajat's background, "
            "skills, projects, experience, education, certifications, leadership, "
            "and contact info. Try asking about one of those topics."
        ),
        "sources": [],
        "mode": "fallback-offtopic",
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def generate(question: str, vectorstore, top_k: int = 4) -> dict:
    """
    Produce a complete response dict (reply, sources, mode) for ``question``
    using only the vectorstore. Always returns a non-empty reply.
    """
    if is_greeting(question):
        import random
        return {
            "reply": random.choice(GREETING_REPLIES),
            "sources": [],
            "mode": "fallback-greeting",
        }

    docs = vectorstore.similarity_search(question.strip(), k=top_k) if vectorstore else []
    intent = detect_intent(question)
    reply, sources = _format_intent_response(intent, question, docs)

    # Off-topic guard: if every retrieved source is a GitHub README
    # (NOT a curated project file) AND the question has no clear intent,
    # the answer is almost certainly not about Rajat.
    if docs and sources and all(s.startswith("github/") for s in sources):
        from retriever.vectorstore import _CONTENT_FILES, _PROJECT_FILES
        valid_sources = _CONTENT_FILES | set(_PROJECT_FILES.keys())
        if not any(s in valid_sources for s in sources):
            if intent in ("general", "what", "how"):
                return _off_topic_response()
        else:
            # Top source IS a valid project/content file — but if the query
            # has no project name and no content keyword, the match is
            # incidental (e.g. "What is FastAPI?" → taskflow.md mentions Docker).
            if intent in ("general", "what", "how"):
                from retriever.vectorstore import _tokens as _vt
                qtokens = set(_vt(question))
                project_names = {
                    "internops", "apogee", "brainbox", "quintern", "taskflow",
                    "tl_management", "secure", "auth", "deloitte", "jpmorgan",
                    "compliance", "copilot",
                }
                content_keywords = {
                    "skill", "stack", "technolog", "framework", "language",
                    "certific", "course", "google", "education", "college",
                    "university", "degree", "svce", "aicte", "pmsss", "scholar",
                    "experience", "uptoskills", "leadership", "ncc", "cadet",
                    "air", "wing", "promotion", "coordinate", "600", "contact",
                    "reach", "email", "phone", "linkedin", "portfolio",
                }
                if not any(any(p in t or t in p for p in project_names) for t in qtokens) \
                   and not any(any(c in t or t in c for c in content_keywords) for t in qtokens):
                    return _off_topic_response()

    if not sources and not docs:
        return _off_topic_response()

    return {
        "reply": (
            f"{reply}\n\n"
            "_— response generated directly from Rajat's knowledge base (no LLM) —_"
        ),
        "sources": sources,
        "mode": f"fallback-{intent}",
    }
