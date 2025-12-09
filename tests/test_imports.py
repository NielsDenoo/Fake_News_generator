"""Test that all modules can be imported successfully."""
import pytest


def test_import_main():
    """Test that main module imports without errors."""
    import main
    assert hasattr(main, 'load_latest_news')
    assert hasattr(main, 'generate_titles_for_session')
    assert hasattr(main, 'select_article')
    assert hasattr(main, 'generate_continuations_for_session')
    assert hasattr(main, 'select_continuation')
    assert hasattr(main, 'generate_final_and_image')


def test_import_schemas():
    """Test that schemas module imports without errors."""
    import schemas
    assert hasattr(schemas, 'Article')


def test_import_app():
    """Test that app module imports without errors."""
    import app
    assert hasattr(app, 'create_dash_app')


def test_import_chains():
    """Test that chain modules import without errors."""
    from chains import title_chain
    from chains import continuation_chain
    from chains import final_story_chain
    from chains import image_chain
    
    assert hasattr(title_chain, 'TitleChain')
    assert hasattr(continuation_chain, 'ContinuationChain')
    assert hasattr(final_story_chain, 'FinalStoryChain')
    assert hasattr(image_chain, 'ImageChain')


def test_import_tools():
    """Test that tools module imports without errors."""
    from tools import news_tool
    assert hasattr(news_tool, 'NewsTool')


def test_import_memory():
    """Test that memory module imports without errors."""
    from memory import session_memory
    assert hasattr(session_memory, 'SessionMemory')
    assert hasattr(session_memory, 'memory')
