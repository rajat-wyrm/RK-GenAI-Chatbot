"""
build_embeddings.py — Pre-computes embeddings for the entire knowledge base
and persists them to data/embeddings.npy + data/chunks.json.

Run once after updating the knowledge base:
    python scripts/build_embeddings.py

Re-running is idempotent: it rebuilds the index from scratch.
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from embeddings import EMBED_DIM, embed_texts  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("build_embeddings")

KB_DIR = ROOT / "knowledge_base"
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
EMB_PATH = DATA_DIR / "embeddings.npy"
CHUNKS_PATH = DATA_DIR / "chunks.json"

# Chunking parameters
MAX_CHARS = 900       # ~225 tokens; small enough to be precise, large enough to be meaningful
MIN_CHARS = 80        # skip tiny fragments
OVERLAP = 120         # context carryover between adjacent chunks

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_WS_RE = re.compile(r"\s+")


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    section: str
    chunk_index: int


def split_markdown(text: str) -> List[tuple[str, str]]:
    """Return list of (section_title, section_text) preserving order."""
    sections: List[tuple[str, str]] = []
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        cleaned = _WS_RE.sub(" ", text).strip()
        if cleaned:
            sections.append(("(intro)", cleaned))
        return sections

    # Text before the first header
    pre = text[: matches[0].start()].strip()
    if pre:
        sections.append((matches[0].group(2).strip(), pre))

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((m.group(2).strip(), body))
    return sections


def chunk_section(title: str, body: str, source: str) -> List[Chunk]:
    """Split a section into overlapping chunks respecting paragraph boundaries."""
    body = _WS_RE.sub(" ", body).strip()
    if len(body) <= MAX_CHARS:
        return [Chunk(id=f"{source}::{title}::0", text=f"{title}\n{body}", source=source,
                      section=title, chunk_index=0)]

    paragraphs = [p.strip() for p in re.split(r"(?<=[.!?])\s+", body) if p.strip()]
    chunks: List[Chunk] = []
    buf: List[str] = []
    buf_len = 0
    idx = 0

    def flush():
        nonlocal buf, buf_len, idx
        if not buf:
            return
        text = " ".join(buf).strip()
        if len(text) >= MIN_CHARS:
            chunks.append(Chunk(
                id=f"{source}::{title}::{idx}",
                text=f"{title}\n{text}",
                source=source,
                section=title,
                chunk_index=idx,
            ))
            idx += 1
        buf.clear()
        buf_len = 0

    for p in paragraphs:
        if buf_len + len(p) + 1 > MAX_CHARS and buf:
            flush()
            # carry overlap from tail of last flushed chunk
            tail = chunks[-1].text if chunks else ""
            if tail and OVERLAP:
                buf.append(tail[-OVERLAP:])
                buf_len = len(buf[-1])
        buf.append(p)
        buf_len += len(p) + 1
    flush()
    return chunks


def load_all_chunks() -> List[Chunk]:
    files = sorted([p for p in KB_DIR.rglob("*.md")])
    log.info(f"found {len(files)} markdown files under {KB_DIR}")
    all_chunks: List[Chunk] = []
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            log.warning(f"skip {fp}: {e}")
            continue
        rel = fp.relative_to(KB_DIR).as_posix()
        for title, body in split_markdown(text):
            all_chunks.extend(chunk_section(title, body, rel))
    log.info(f"produced {len(all_chunks)} chunks")
    return all_chunks


def main() -> int:
    chunks = load_all_chunks()
    if not chunks:
        log.error("no chunks produced; check knowledge_base/")
        return 1

    texts = [c.text for c in chunks]
    log.info(f"embedding {len(texts)} chunks via HF Inference API...")
    vecs = embed_texts(texts)
    arr = np.asarray(vecs, dtype=np.float32)
    if arr.shape[1] != EMBED_DIM:
        log.error(f"unexpected embedding dim: {arr.shape}")
        return 1

    # L2-normalize so dot product == cosine similarity
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms

    np.save(EMB_PATH, arr)
    CHUNKS_PATH.write_text(
        json.dumps([asdict(c) for c in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info(f"saved {arr.shape[0]} x {arr.shape[1]} embeddings to {EMB_PATH}")
    log.info(f"saved chunk metadata to {CHUNKS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
