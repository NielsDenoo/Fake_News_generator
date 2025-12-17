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
    
    def get_all_sessions(self) -> Dict[str, Dict]:
        """Get info about all active sessions for history view."""
        with self._lock:
            sessions = {}
            for sid, state in self._store.items():
                # Create a display name
                if state.session_name:
                    name = state.session_name
                elif state.articles and len(state.articles) > 0:
                    # Use first article title as name
                    name = state.articles[0].title[:50] + "..."
                else:
                    name = f"Session {sid[:8]}"
                
                # Create summary
                if state.is_complete:
                    summary = "✅ Completed story"
                elif state.continuation_options:
                    summary = "📝 Ready to generate story"
                elif state.articles:
                    summary = f"📰 {len(state.articles)} articles loaded"
                else:
                    summary = "🆕 New session"
                
                sessions[sid] = {
                    "session_id": sid,
                    "session_name": name,
                    "summary": summary,
                    "created_at": state.created_at.isoformat(),
                    "last_accessed": state.last_accessed.isoformat(),
                    "is_complete": state.is_complete,
                    "has_story": state.final_story is not None,
                }
            
            # Sort by last accessed (newest first)
            sorted_sessions = dict(
                sorted(sessions.items(), 
                       key=lambda x: x[1]["last_accessed"], 
                       reverse=True)
            )
            return sorted_sessions


memory = SessionMemory(timeout_minutes=60)


__all__ = ["memory", "SessionMemory"]