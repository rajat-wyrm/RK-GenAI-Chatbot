"""
vectorstore.py — Retrieval over the personal knowledge base.

Two modes:
  1. Embedding-based (preferred): uses Hugging Face Inference API for query
     embeddings and numpy cosine similarity over pre-computed KB vectors
     stored in data/embeddings.npy + data/chunks.json.
  2. Keyword fallback: simple token overlap scoring, used when no embedding
     index is available (e.g. HF key not configured or build hasn't run).

Both modes return objects exposing `.page_content` and `.metadata` so the
agent nodes can use them interchangeably (duck-typed langchain Document).
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger("skillnova.retriever")

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "knowledge_base"
DATA_DIR = ROOT / "data"
EMB_PATH = DATA_DIR / "embeddings.npy"
CHUNKS_PATH = DATA_DIR / "chunks.json"

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Doc:
    page_content: str
    metadata: dict = field(default_factory=dict)


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


# ---------------------------------------------------------------------------
# Embedding-based vector store
# ---------------------------------------------------------------------------
class EmbeddingVectorStore:
    """Cosine-similarity search over pre-computed KB embeddings."""

    def __init__(self, matrix: np.ndarray, chunks: list[dict]):
        self.matrix = matrix  # shape (n, d), L2-normalised
        self.chunks = chunks
        logger.info(f"[VECTORSTORE] Loaded {matrix.shape[0]} pre-computed embeddings")

    def similarity_search(self, query: str, k: int = 5) -> List[Doc]:
        if self.matrix.shape[0] == 0:
            return []
        from embeddings import embed_query
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                qvec = ex.submit(embed_query, query).result(timeout=15)
        except Exception as e:
            logger.warning(f"[VECTORSTORE] embed_query failed: {e}")
            return []
        if not qvec:
            return []
        q = np.asarray(qvec, dtype=np.float32)
        n = np.linalg.norm(q)
        if n == 0:
            return []
        q = q / n
        scores = self.matrix @ q  # cosine similarity (vectors are normalised)
        top_idx = np.argsort(scores)[::-1][: max(k * 3, k)]
        qset = set(_tokens(query))
        intent_target = _detect_intent_target(qset)
        raw = []
        for i in top_idx:
            c = self.chunks[int(i)]
            src = c["source"]
            base = float(scores[int(i)])
            boost = _source_boost(src, qset)
            raw.append((base * boost, c, src))
        raw.sort(key=lambda x: x[0], reverse=True)
        if intent_target:
            # Force the target file's best chunk into the results
            all_chunks_for_target = [
                c for c in self.chunks if c["source"] == intent_target
            ]
            if all_chunks_for_target and not any(c["source"] == intent_target for _, c, _ in raw):
                raw = [(1.0, all_chunks_for_target[0], intent_target)] + raw
            target = [(s, c, src) for s, c, src in raw if src == intent_target]
            others = [(s, c, src) for s, c, src in raw if src != intent_target]
            raw = target + others
        docs: List[Doc] = []
        for _, c, src in raw[:k]:
            docs.append(Doc(
                page_content=c["text"],
                metadata={"source": src, "section": c.get("section", ""),
                          "chunk": c.get("chunk_index", 0), "score": float(scores[int(_)])} if False else {"source": src, "section": c.get("section", ""), "chunk": c.get("chunk_index", 0)},
            ))
        return docs


async def _embed_query_sync(query: str) -> List[float]:
    from embeddings import embed_query
    return embed_query(query)


def _load_embedding_store() -> Optional[EmbeddingVectorStore]:
    if not (EMB_PATH.exists() and CHUNKS_PATH.exists()):
        return None
    try:
        matrix = np.load(EMB_PATH)
        chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"[VECTORSTORE] failed to load embedding cache: {e}")
        return None
    if matrix.ndim != 2 or matrix.shape[0] != len(chunks):
        logger.warning("[VECTORSTORE] embedding cache shape mismatch")
        return None
    return EmbeddingVectorStore(matrix, chunks)


# ---------------------------------------------------------------------------
# Source boosting — content files (profile/skills/projects/etc.) outrank
# generic GitHub READMEs which contain a lot of boilerplate text.
# ---------------------------------------------------------------------------
_CONTENT_FILES = {
    "profile.md", "skills.md", "projects.md", "experience.md",
    "education.md", "certifications.md", "leadership.md", "contact.md",
}
_PROJECT_FILES = {
    "github/InternOps.md": 3.0,
    "github/apogee.md": 2.5,
    "github/ai-compliance-copilot.md": 2.5,
    "github/brainbox-ai.md": 2.0,
    "github/Quintern.md": 2.0,
    "github/taskflow.md": 2.0,
    "github/TL_management-.md": 2.0,
    "github/secure-auth-backend.md": 1.5,
    "github/rajat-portfolio.md": 1.5,
}


# Intent keywords → preferred content file. When the query contains any of
# these words, the matching file gets a strong boost.
_INTENT_BOOST = {
    # Category → content file (specific keywords only — no generic fillers)
    "skill":            "skills.md",
    "stack":            "skills.md",
    "technolog":        "skills.md",
    "framework":        "skills.md",
    "language":         "skills.md",
    "certific":         "certifications.md",
    "course":           "certifications.md",
    "google":           "certifications.md",
    "jpmorgan":         "certifications.md",
    "education":        "education.md",
    "college":          "education.md",
    "university":       "education.md",
    "degree":           "education.md",
    "svce":             "education.md",
    "aicte":            "education.md",
    "pmsss":            "education.md",
    "scholar":          "education.md",
    "experience":       "experience.md",
    "uptoskills":       "experience.md",
    "team lead":        "experience.md",
    "senior tl":        "experience.md",
    "promotion":        "experience.md",
    "leadership":       "leadership.md",
    "ncc":              "leadership.md",
    "cadet":            "leadership.md",
    "air wing":         "leadership.md",
    "coordinate":       "leadership.md",
    "600":              "leadership.md",
    "contact":          "contact.md",
    "reach":            "contact.md",
    "email":            "contact.md",
    "phone":            "contact.md",
    "linkedin":         "contact.md",
    "portfolio":        "contact.md",
    # Project names → their repo files (most specific — checked first by scoring)
    "internops":        "github/InternOps.md",
    "apogee":           "github/apogee.md",
    "compliance":       "github/ai-compliance-copilot.md",
    "copilot":          "github/ai-compliance-copilot.md",
    "brainbox":         "github/brainbox-ai.md",
    "quintern":         "github/Quintern.md",
    "taskflow":         "github/taskflow.md",
    "tl_management":    "github/TL_management-.md",
    "secure-auth":      "github/secure-auth-backend.md",
    "deloitte":         "github/deloitte-iot-task.md",
}


def _source_boost(source: str, query_tokens: set[str]) -> float:
    """Return a multiplier for a chunk's score based on its source and the query."""
    if not source:
        return 1.0

    # 1) Exact project-file match (e.g. github/InternOps.md)
    if source in _PROJECT_FILES:
        return _PROJECT_FILES[source]

    # 2) Intent-based boost — if any query token matches an intent keyword
    #    (prefix or substring), the mapped file gets a very strong boost.
    name = source.split("/")[-1]
    full_name = source  # e.g. "github/InternOps.md"
    for token in query_tokens:
        for intent_key, target_file in _INTENT_BOOST.items():
            # Accept either exact source name or "github/<filename>" forms
            if target_file != name and target_file != full_name:
                continue
            if " " in intent_key:
                if intent_key in token:
                    return 10.0
            else:
                if token == intent_key or token.startswith(intent_key) or intent_key.startswith(token):
                    return 10.0

    # 3) Named content files (profile, skills, projects, ...)
    if source in _CONTENT_FILES:
        base = name.replace(".md", "")
        if any(t == base or base in t for t in query_tokens):
            return 4.0  # filename token match
        return 2.0

    # 4) GitHub profile / portfolio / generic
    if source.startswith("github/_"):
        return 0.4
    if source.startswith("github/"):
        return 0.5
    return 1.0


def _detect_intent_target(query_tokens: set[str]) -> Optional[str]:
    """Return the source file that best matches the query's intent.

    Scores by specificity: exact token match > prefix > reverse prefix,
    and longer intent keys beat shorter ones (more specific).
    """
    best_target: Optional[str] = None
    best_score = 0
    for intent_key, target_file in _INTENT_BOOST.items():
        for token in query_tokens:
            score = 0
            if " " in intent_key:
                if intent_key in token:
                    score = 40 + len(intent_key)
            else:
                if token == intent_key:
                    score = 100 + len(intent_key)
                elif token.startswith(intent_key):
                    score = 60 + len(intent_key)
                elif intent_key.startswith(token):
                    score = 30 + len(intent_key)
            if score > best_score:
                best_score = score
                best_target = target_file
    return best_target


def _force_include_target(all_docs: list, intent_target: str, results: list) -> list:
    """If the intent target file exists in the corpus, ensure at least one of its
    chunks is in the results, even if its keyword score was low."""
    if not intent_target:
        return results
    if any(d.metadata.get("source") == intent_target for d in results):
        return results
    # Find the best chunk for the target file and prepend it
    candidates = [d for d in all_docs if d.metadata.get("source") == intent_target]
    if candidates:
        return [candidates[0]] + results
    return results


# ---------------------------------------------------------------------------
# Keyword fallback (same surface area)
# ---------------------------------------------------------------------------
class KeywordVectorStore:
    def __init__(self, docs: List[Doc]):
        self.docs = docs
        self._doc_tokens = [_tokens(d.page_content) for d in docs]
        self._doc_tsets = [set(t) for t in self._doc_tokens]
        logger.info(f"[VECTORSTORE] Keyword index over {len(docs)} chunks")

    def similarity_search(self, query: str, k: int = 5) -> List[Doc]:
        qset = set(_tokens(query))
        if not qset or not self.docs:
            return self.docs[:k]

        intent_target = _detect_intent_target(qset)

        scored = []
        for i, (doc, tokens, tset) in enumerate(zip(self.docs, self._doc_tokens, self._doc_tsets)):
            if not tokens:
                continue
            overlap = len(qset & tset)
            if overlap == 0:
                continue
            base = overlap / (len(tset) ** 0.5)
            boost = _source_boost(doc.metadata.get("source", ""), qset)
            scored.append((base * boost, i, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [d for _, _, d in scored[: max(k * 3, k)]]

        # Force intent-matched file to the top (and ensure it's present)
        if intent_target:
            results = _force_include_target(self.docs, intent_target, results)
            target_docs = [d for d in results if d.metadata.get("source") == intent_target]
            other_docs = [d for d in results if d.metadata.get("source") != intent_target]
            results = target_docs + other_docs

        if not results:
            results = self.docs[:k]
        for d in results:
            d.metadata.setdefault("source", "unknown")
        return results[:k]


def _split_chunks(text: str, source: str) -> List[Doc]:
    chunks: List[Doc] = []
    sections: list[tuple[str, str]] = []
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        body = text.strip()
        if body:
            chunks.append(Doc(page_content=body, metadata={"source": source, "chunk": 0}))
        return chunks

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((m.group(2).strip(), body))

    for idx, (title, body) in enumerate(sections):
        chunks.append(Doc(
            page_content=f"{title}\n{body}",
            metadata={"source": source, "section": title, "chunk": idx},
        ))
    return chunks


def _build_keyword_store() -> KeywordVectorStore:
    docs: List[Doc] = []
    if KB_DIR.is_dir():
        for fp in sorted(KB_DIR.rglob("*.md")):
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError as e:
                logger.warning(f"[VECTORSTORE] cannot read {fp}: {e}")
                continue
            rel = fp.relative_to(KB_DIR).as_posix()
            docs.extend(_split_chunks(text, rel))
    if not docs:
        logger.warning("[VECTORSTORE] knowledge_base empty")
    return KeywordVectorStore(docs)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
class _HybridStore:
    """Embedding store front-end; falls back to keyword if embedding is empty."""

    def __init__(self, primary, fallback: KeywordVectorStore):
        self.primary = primary
        self.fallback = fallback

    def similarity_search(self, query: str, k: int = 5) -> List[Doc]:
        if self.primary is not None and self.primary.matrix.shape[0] > 0:
            try:
                return self.primary.similarity_search(query, k=k)
            except Exception as e:
                logger.warning(f"[VECTORSTORE] embedding search failed, using keyword: {e}")
        return self.fallback.similarity_search(query, k=k)


def build_vectorstore():
    primary = _load_embedding_store()
    fallback = _build_keyword_store()
    if primary is None:
        logger.info("[VECTORSTORE] No embedding cache found — using keyword index. "
                    "Run `python scripts/build_embeddings.py` to enable semantic search.")
    else:
        logger.info("[VECTORSTORE] Using embedding-based retrieval (semantic).")
    return _HybridStore(primary, fallback)
