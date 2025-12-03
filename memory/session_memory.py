from typing import Dict
from threading import Lock
from schemas import SessionState


class SessionMemory:
    """In-memory per-session storage."""

    def __init__(self):
        self._store: Dict[str, SessionState] = {}
        self._lock = Lock()

    def get(self, session_id: str) -> SessionState:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = SessionState()
            return self._store[session_id]

    def set(self, session_id: str, state: SessionState) -> None:
        with self._lock:
            self._store[session_id] = state

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._store[session_id] = SessionState()


memory = SessionMemory()


__all__ = ["memory", "SessionMemory"]