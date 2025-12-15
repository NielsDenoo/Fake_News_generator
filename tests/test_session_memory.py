"""Tests for session memory management."""
import pytest
import time
from datetime import datetime, timedelta
from memory.session_memory import SessionMemory, SessionState


def test_session_memory_init():
    """Test SessionMemory initialization."""
    memory = SessionMemory()
    assert isinstance(memory._store, dict)
    assert len(memory._store) == 0


def test_session_memory_set_and_get():
    """Test setting and getting session state."""
    memory = SessionMemory()
    session_id = "test_session_123"
    
    # Create state with initial data
    state = SessionState(final_story="Test story")
    
    memory.set(session_id, state)
    retrieved = memory.get(session_id)
    
    assert retrieved is not None
    assert retrieved.final_story == "Test story"


def test_session_memory_get_nonexistent():
    """Test getting a non-existent session creates new state."""
    memory = SessionMemory()
    session_id = "nonexistent_session"
    
    state = memory.get(session_id)
    assert state is not None
    assert isinstance(state, SessionState)


def test_session_state_defaults():
    """Test SessionState default values."""
    state = SessionState()
    assert state.articles == []
    assert state.selected_article_index is None
    assert state.continuation_options == []
    assert state.selected_continuation_index is None
    assert state.final_story is None
    assert state.image_base64 is None
    # Test new timestamp fields
    assert isinstance(state.created_at, datetime)
    assert isinstance(state.last_accessed, datetime)


def test_session_expiration():
    """Test that sessions expire after timeout."""
    memory = SessionMemory(timeout_minutes=0.01)  # 0.6 seconds timeout
    session_id = "test_expire"
    
    # Create session
    state = memory.get(session_id)
    assert session_id in memory._store
    
    # Wait for expiration
    time.sleep(1)
    
    # Trigger cleanup
    cleaned = memory.cleanup_now()
    assert cleaned == 1
    assert session_id not in memory._store


def test_session_last_accessed_update():
    """Test that last_accessed is updated on get()."""
    memory = SessionMemory()
    session_id = "test_access"
    
    # Create session
    state1 = memory.get(session_id)
    first_access = state1.last_accessed
    
    # Wait a bit
    time.sleep(0.1)
    
    # Access again
    state2 = memory.get(session_id)
    second_access = state2.last_accessed
    
    assert second_access > first_access


def test_get_stats():
    """Test session statistics."""
    memory = SessionMemory()
    
    # Create some sessions
    for i in range(3):
        memory.get(f"session_{i}")
    
    stats = memory.get_stats()
    
    assert stats["active_sessions"] == 3
    assert stats["estimated_memory_bytes"] > 0
    assert stats["estimated_memory_mb"] >= 0
    assert "timeout_minutes" in stats


def test_manual_cleanup():
    """Test manual cleanup function."""
    memory = SessionMemory(timeout_minutes=0.01)
    
    # Create sessions
    memory.get("session_1")
    memory.get("session_2")
    
    assert len(memory._store) == 2
    
    # Wait for expiration
    time.sleep(1)
    
    # Cleanup
    cleaned = memory.cleanup_now()
    assert cleaned == 2
    assert len(memory._store) == 0
