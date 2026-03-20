"""
In-memory chat-session store.

Implements the tiny surface area of a SQLAlchemy session that ``main.py``
relies on, so the chatbot runs without an external database.

Exposed:
- ``SessionLocal()``  — factory returning a handle with ``.query(ChatSession)``.
- ``ChatSession``     — model with the fields used by main.py.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import List


_lock = threading.Lock()

_sessions: List["ChatSession"] = []


@dataclass
class ChatSession:
    session_id: str = ""
    user_message: str = ""
    bot_response: str = ""
    turn_number: int = 0
    id: int = 0


class _Query:
    def __init__(self, model):
        self._model = model
        self._filters = {}
        self._order_by_field = None
        self._limit = None

    def filter_by(self, **kwargs):
        self._filters.update(kwargs)
        return self

    def order_by(self, field_name):
        # Accept a string ("turn_number") or a dataclass Field descriptor
        # (ChatSession.turn_number) — extract its .name in the latter case.
        name = getattr(field_name, "name", None)
        if not isinstance(name, str):
            name = str(field_name)
        self._order_by_field = name
        return self

    def limit(self, n):
        self._limit = n
        return self

    def all(self) -> List[ChatSession]:
        rows = [r for r in _sessions if isinstance(r, self._model)]
        for k, v in self._filters.items():
            rows = [r for r in rows if getattr(r, k, None) == v]
        if self._order_by_field is not None:
            rows.sort(key=lambda r: getattr(r, self._order_by_field, 0))
        if self._limit is not None:
            rows = rows[: self._limit]
        return rows

    def count(self) -> int:
        rows = [r for r in _sessions if isinstance(r, self._model)]
        for k, v in self._filters.items():
            rows = [r for r in rows if getattr(r, k, None) == v]
        return len(rows)


class _Session:
    def __init__(self):
        self._added: List[ChatSession] = []

    def query(self, model):
        return _Query(model)

    def add(self, obj: ChatSession):
        self._added.append(obj)

    def commit(self):
        with _lock:
            for obj in self._added:
                obj.id = len(_sessions) + 1
                _sessions.append(obj)
        self._added.clear()

    def close(self):
        self._added.clear()


def SessionLocal() -> _Session:
    return _Session()
