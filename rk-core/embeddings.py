"""
embeddings.py — Hugging Face Inference API embeddings client.

Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim, fast, high quality).
Implemented with `requests` (stdlib-friendly sync client) so it works on
all Python versions including 3.14 where httpx has occasional SSL issues.
The vectorstore wraps calls in a thread to keep FastAPI's event loop
non-blocked.
"""
from __future__ import annotations

import logging
import os
from typing import List

import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")
logger = logging.getLogger("skillnova.embeddings")

HF_API = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384

_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def _get_token() -> str:
    return (os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACE_TOKEN") or "").strip()


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts. Returns a list of 384-dim vectors."""
    if not texts:
        return []
    token = _get_token()
    if not token:
        raise RuntimeError(
            "HUGGINGFACE_API_KEY is not set. Add it to .env to enable RAG embeddings."
        )

    session = _get_session()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    BATCH = 32
    all_vecs: List[List[float]] = []
    for i in range(0, len(texts), BATCH):
        chunk = [t if t.strip() else " " for t in texts[i : i + BATCH]]
        payload = {"inputs": chunk, "options": {"wait_for_model": True}}
        r = session.post(HF_API, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            logger.error(f"[EMBED] HF {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
        vecs = r.json()
        if not isinstance(vecs, list) or not vecs or not isinstance(vecs[0], list):
            raise RuntimeError(f"Unexpected embedding response shape: {type(vecs)}")
        all_vecs.extend(vecs)
    return all_vecs


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]
