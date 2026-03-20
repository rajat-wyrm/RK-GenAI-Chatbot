"""
llm package — multi-provider LLM layer with parallel racing.

Public surface:
    get_llm_response(prompt) -> str
        Synchronous, runs all enabled providers in parallel and returns the
        fastest successful response. Backed by `llm.race.race_chat`.

    stream_chat(prompt) -> AsyncIterator[tuple[str, str]]
        Async streaming from the fastest streaming provider (Groq by default),
        with graceful fallback to racing on failure.

    CircuitBreaker, RateLimiter
        Re-exported for use by tools and callers that need their own protection.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import AsyncIterator, Optional

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger("skillnova.llm")


# ---------------------------------------------------------------------------
# Circuit breaker (reused by tools)
# ---------------------------------------------------------------------------
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "closed"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
                return True
            return False
        return True


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, min_interval: float = 0.05):
        self.min_interval = min_interval
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        delta = now - self.last_call
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self.last_call = time.time()


# ---------------------------------------------------------------------------
# Sync entry point — parallel race across all enabled providers
# ---------------------------------------------------------------------------
def get_llm_response(prompt: str) -> str:
    """
    Synchronously call all enabled LLM providers in parallel and return the
    fastest successful response. Falls back to a safe error message if all
    providers fail.
    """
    try:
        from llm.race import race_chat
        _, text, ms = asyncio.run(race_chat(prompt))
        logger.info(f"[LLM] race winner in {ms:.0f}ms ({len(text)} chars)")
        return text
    except Exception as e:
        logger.exception(f"[LLM] race failed: {e}")
        return "AI service unavailable. Try again later."


async def aget_llm_response(prompt: str, question: Optional[str] = None,
                           vectorstore=None) -> tuple[str, str, float]:
    """Async variant returning (provider_name, text, latency_ms).

    If every LLM provider fails, falls back to the KB-only response generator
    so the chatbot is always available.
    """
    from llm.race import race_chat
    return await race_chat(prompt, question=question, vectorstore=vectorstore)


async def stream_chat(prompt: str) -> AsyncIterator[tuple[str, str]]:
    """Async stream of (provider_name, token) tuples."""
    from llm.race import stream_chat as _stream
    async for n, t in _stream(prompt):
        yield n, t


__all__ = [
    "CircuitBreaker",
    "RateLimiter",
    "get_llm_response",
    "aget_llm_response",
    "stream_chat",
]
