"""Tiny in-memory TTL cache (Redis-compatible interface)."""

from __future__ import annotations

import threading
import time
from typing import Optional, Tuple


class InMemoryCache:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if expires_at and expires_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value, ttl: int = 300) -> None:
        expires_at = time.time() + ttl if ttl else 0
        with self._lock:
            self._store[key] = (value, expires_at)


def create_cache(redis_enabled: bool = False) -> Tuple[InMemoryCache, None]:
    """Create a cache backend. The second tuple element mirrors the original API."""
    if redis_enabled:
        # Real Redis support intentionally not wired in this build.
        pass
    return InMemoryCache(), None
