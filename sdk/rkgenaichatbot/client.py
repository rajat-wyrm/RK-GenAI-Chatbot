"""
RK Gen AI Chatbot — Python client (sync + async).

Tiny wrapper around the backend's REST + SSE endpoints. The only runtime
dependency is `httpx`.
"""
from __future__ import annotations

import json
import os
import uuid
from typing import AsyncIterator, Iterator, Optional

import httpx

DEFAULT_API_URL = os.getenv("RK_CHATBOT_API_URL", "http://localhost:5000")


def _parse_sse_events(buffer: str) -> tuple[list[dict], str]:
    events, buf = [], buffer
    while "\n\n" in buf:
        raw, buf = buf.split("\n\n", 1)
        for line in raw.split("\n"):
            if line.startswith("data: "):
                try:
                    events.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    continue
    return events, buf


class _BaseChatbot:
    def __init__(self, api_url: str = DEFAULT_API_URL, timeout: float = 60.0):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.session_id: Optional[str] = None

    def _ensure_session(self) -> str:
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        return self.session_id


class Chatbot(_BaseChatbot):
    """Synchronous client."""

    def health(self) -> dict:
        with httpx.Client(timeout=10) as c:
            r = c.get(f"{self.api_url}/api/health")
            r.raise_for_status()
            return r.json()

    def create_session(self) -> str:
        with httpx.Client(timeout=10) as c:
            r = c.get(f"{self.api_url}/api/session")
            r.raise_for_status()
            self.session_id = r.json()["session_id"]
            return self.session_id

    def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        sid = session_id or self.session_id or self._ensure_session()
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(
                f"{self.api_url}/api/integrate/chat",
                json={"message": message, "session_id": sid},
            )
            r.raise_for_status()
            data = r.json()
            if data.get("session_id"):
                self.session_id = data["session_id"]
            return data

    def stream(self, message: str, session_id: Optional[str] = None) -> Iterator[str]:
        sid = session_id or self.session_id or self._ensure_session()
        with httpx.Client(timeout=self.timeout) as c:
            with c.stream(
                "POST",
                f"{self.api_url}/api/integrate/stream",
                json={"message": message, "session_id": sid},
            ) as r:
                r.raise_for_status()
                buffer = ""
                for chunk in r.iter_text():
                    if not chunk:
                        continue
                    buffer += chunk
                    events, buffer = _parse_sse_events(buffer)
                    for ev in events:
                        etype = ev.get("type")
                        if etype == "token":
                            yield ev.get("content", "")
                        elif etype == "sources":
                            pass  # available in chat() response
                        elif etype == "done":
                            if ev.get("session_id"):
                                self.session_id = ev["session_id"]
                            return
                        elif etype == "error":
                            raise RuntimeError(ev.get("message", "stream error"))


class AsyncChatbot(_BaseChatbot):
    """Async client (httpx.AsyncClient)."""

    async def _client(self) -> httpx.AsyncClient:
        if not hasattr(self, "_http") or self._http is None:
            self._http = httpx.AsyncClient(timeout=self.timeout)
        return self._http

    async def aclose(self) -> None:
        if getattr(self, "_http", None) is not None:
            await self._http.aclose()
            self._http = None

    async def health(self) -> dict:
        c = await self._client()
        r = await c.get(f"{self.api_url}/api/health")
        r.raise_for_status()
        return r.json()

    async def create_session(self) -> str:
        c = await self._client()
        r = await c.get(f"{self.api_url}/api/session")
        r.raise_for_status()
        self.session_id = r.json()["session_id"]
        return self.session_id

    async def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        sid = session_id or self.session_id or self._ensure_session()
        c = await self._client()
        r = await c.post(
            f"{self.api_url}/api/integrate/chat",
            json={"message": message, "session_id": sid},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("session_id"):
            self.session_id = data["session_id"]
        return data

    async def stream(self, message: str, session_id: Optional[str] = None) -> AsyncIterator[str]:
        sid = session_id or self.session_id or self._ensure_session()
        c = await self._client()
        async with c.stream(
            "POST",
            f"{self.api_url}/api/integrate/stream",
            json={"message": message, "session_id": sid},
        ) as r:
            r.raise_for_status()
            buffer = ""
            async for chunk in r.aiter_text():
                if not chunk:
                    continue
                buffer += chunk
                events, buffer = _parse_sse_events(buffer)
                for ev in events:
                    etype = ev.get("type")
                    if etype == "token":
                        yield ev.get("content", "")
                    elif etype == "done":
                        if ev.get("session_id"):
                            self.session_id = ev["session_id"]
                        return
                    elif etype == "error":
                        raise RuntimeError(ev.get("message", "stream error"))
