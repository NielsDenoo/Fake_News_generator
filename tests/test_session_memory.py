"""Tests for session memory management."""
import pytest
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
