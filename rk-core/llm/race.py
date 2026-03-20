"""
race.py — Parallel multi-provider LLM racing with always-on fallback.

Fires all enabled providers simultaneously and returns the first successful
response. If every provider fails, delegates to the KB-only fallback so the
chatbot is *never* unavailable.

For streaming, delegates to the provider's `stream` function (currently Groq).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import AsyncIterator, Optional

from llm import providers

logger = logging.getLogger("skillnova.race")

RACE_TIMEOUT_S = float(os.getenv("LLM_RACE_TIMEOUT_S", "20"))


async def _call_one(name: str, prompt: str, temperature: float) -> tuple[str, str, float]:
    fn = providers.PROVIDER_CHAT.get(name)
    if fn is None:
        raise RuntimeError(f"unknown provider: {name}")
    t0 = time.perf_counter()
    text = await fn(prompt, temperature=temperature)
    elapsed = (time.perf_counter() - t0) * 1000
    return name, text, elapsed


async def race_chat(prompt: str, temperature: float = 0.3,
                    providers_filter: Optional[list[str]] = None,
                    timeout: float = RACE_TIMEOUT_S,
                    question: Optional[str] = None,
                    vectorstore=None) -> tuple[str, str, float]:
    """
    Fire all enabled providers in parallel, return (name, text, latency_ms)
    of the first success. Cancels remaining tasks once a winner is found.

    If every provider fails, falls back to the KB-only response generator
    so the chatbot is always available.
    """
    names = providers_filter or providers.enabled_providers()
    if not names:
        logger.warning("[RACE] no LLM providers configured — using KB fallback")
        return await _fallback_response(question or prompt, vectorstore, provider="kb-fallback")

    tasks = [asyncio.create_task(_call_one(n, prompt, temperature), name=n) for n in names]
    deadline = time.perf_counter() + timeout
    errors: dict[str, str] = {}
    winner_text: Optional[str] = None
    winner_name = ""
    winner_ms = 0.0

    # Wait for the first SUCCESS, falling through to subsequent completions
    # if earlier ones failed or returned empty. This is the key fix:
    # a fast-failing provider (e.g. 401) must not prevent slower providers
    # from being tried.
    while tasks:
        remaining = max(0.05, deadline - time.perf_counter())
        try:
            done, pending = await asyncio.wait(
                tasks, timeout=remaining, return_when=asyncio.FIRST_COMPLETED
            )
        except asyncio.TimeoutError:
            break
        for t in done:
            try:
                n, text, ms = t.result()
                if text and text.strip():
                    winner_text = text.strip()
                    winner_name = n
                    winner_ms = ms
                    break
            except Exception as e:
                errors[t.get_name()] = str(e)[:120]
        if winner_text is not None:
            break
        tasks = list(pending)

    # Cancel anything still running
    for t in tasks:
        t.cancel()

    if winner_text is None:
        logger.error(f"[RACE] all providers failed: {errors} — using KB fallback")
        return await _fallback_response(question or prompt, vectorstore,
                                       provider="kb-fallback", errors=errors)

    logger.info(f"[RACE] winner={winner_name} latency={winner_ms:.0f}ms")
    return winner_name, winner_text, winner_ms


async def _fallback_response(question: str, vectorstore, provider: str = "kb-fallback",
                             errors: Optional[dict] = None) -> tuple[str, str, float]:
    """Generate a KB-only response. Always succeeds."""
    from fallback import generate
    t0 = time.perf_counter()
    # `generate` is sync; run it in a thread to keep the event loop free
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, generate, question, vectorstore)
    elapsed = (time.perf_counter() - t0) * 1000
    if errors:
        logger.info(f"[FALLBACK] served KB-only response in {elapsed:.0f}ms (LLM errors: {len(errors)})")
    else:
        logger.info(f"[FALLBACK] served KB-only response in {elapsed:.0f}ms")
    return provider, result["reply"], elapsed


async def stream_chat(prompt: str, temperature: float = 0.3,
                      provider: str = "groq") -> AsyncIterator[tuple[str, str]]:
    """
    Stream tokens from a single provider. Yields (provider_name, token) tuples.
    Falls back to racing if the streaming provider fails.
    """
    fn = providers.PROVIDER_STREAM.get(provider)
    if fn is None:
        # No streaming for this provider — race and yield the whole reply at once
        name, text, _ = await race_chat(prompt, temperature=temperature)
        yield name, text
        return

    try:
        async for token in fn(prompt, temperature=temperature):
            yield provider, token
    except Exception as e:
        logger.warning(f"[STREAM] {provider} failed ({e}), falling back to race")
        name, text, _ = await race_chat(prompt, temperature=temperature)
        yield name, text
