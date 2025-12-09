"""Tests for the NewsAPI tool."""
import pytest
from tools.news_tool import NewsTool, Article


def test_news_tool_init():
    """Test NewsTool initialization."""
    tool = NewsTool(api_key="test_key")
    assert tool.api_key == "test_key"
    assert tool.country == "us"


def test_news_tool_init_with_country():
    """Test NewsTool initialization with custom country."""
    tool = NewsTool(api_key="test_key", country="gb")
    assert tool.country == "gb"


def test_news_tool_categories():
    """Test that NewsTool has expected categories."""
    assert "business" in NewsTool.CATEGORIES
    assert "entertainment" in NewsTool.CATEGORIES
    assert "technology" in NewsTool.CATEGORIES
    assert "science" in NewsTool.CATEGORIES
    assert "sports" in NewsTool.CATEGORIES
    assert "health" in NewsTool.CATEGORIES
    assert "general" in NewsTool.CATEGORIES


def test_article_dataclass():
    """Test Article dataclass creation."""
    article = Article(
        title="Test Title",
        description="Test Description",
        url="https://example.com",
        content="Test Content"
    )
    assert article.title == "Test Title"
    assert article.description == "Test Description"
    assert str(article.url) == "https://example.com/"  # HttpUrl adds trailing slash
    assert article.content == "Test Content"
