from typing import Dict, List
from threading import Lock
from datetime import datetime, timedelta
from schemas import SessionState


class SessionMemory:
    """In-memory per-session storage with automatic expiration."""

    def __init__(self, timeout_minutes: int = 60):
        self._store: Dict[str, SessionState] = {}
        self._lock = Lock()
        self.timeout = timedelta(minutes=timeout_minutes)
        self._last_cleanup = datetime.now()

    def get(self, session_id: str) -> SessionState:
        with self._lock:
            # Periodic cleanup (every 5 minutes)
            if (datetime.now() - self._last_cleanup).total_seconds() > 300:
                self._cleanup_expired_sessions()
            
            if session_id not in self._store:
                self._store[session_id] = SessionState()
            else:
                # Update last accessed time
                self._store[session_id].last_accessed = datetime.now()
            return self._store[session_id]

    def set(self, session_id: str, state: SessionState) -> None:
        with self._lock:
            self._store[session_id] = state

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._store[session_id] = SessionState()
    
    def _cleanup_expired_sessions(self) -> int:
        """Remove sessions older than timeout. Called internally."""
        now = datetime.now()
        expired = [
            sid for sid, state in self._store.items()
            if now - state.last_accessed > self.timeout
        ]
        for sid in expired:
            del self._store[sid]
        
        self._last_cleanup = now
        if expired:
            print(f"[SessionMemory] Cleaned up {len(expired)} expired session(s)")
        return len(expired)
    
    def cleanup_now(self) -> int:
        """Manually trigger cleanup of expired sessions."""
        with self._lock:
            return self._cleanup_expired_sessions()
    
    def get_stats(self) -> Dict[str, any]:
        """Get session statistics."""
        with self._lock:
            now = datetime.now()
            active_sessions = len(self._store)
            total_memory = sum(
                len(str(state.dict()).encode('utf-8')) 
                for state in self._store.values()
            )
            
            # Age distribution
            ages = [(now - state.created_at).total_seconds() for state in self._store.values()]
            avg_age = sum(ages) / len(ages) if ages else 0
            
            return {
                "active_sessions": active_sessions,
                "estimated_memory_bytes": total_memory,
                "estimated_memory_mb": round(total_memory / 1024 / 1024, 2),
                "average_session_age_seconds": round(avg_age, 2),
                "timeout_minutes": self.timeout.total_seconds() / 60,
            }


memory = SessionMemory(timeout_minutes=60)


__all__ = ["memory", "SessionMemory"]