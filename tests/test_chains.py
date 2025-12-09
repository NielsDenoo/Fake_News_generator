"""Tests for chain modules initialization."""
import pytest
import os


def test_title_chain_init():
    """Test TitleChain can be initialized."""
    from chains.title_chain import TitleChain
    chain = TitleChain()
    assert chain is not None


def test_continuation_chain_init():
    """Test ContinuationChain can be initialized."""
    from chains.continuation_chain import ContinuationChain
    chain = ContinuationChain()
    assert chain is not None


def test_final_story_chain_init():
    """Test FinalStoryChain can be initialized."""
    from chains.final_story_chain import FinalStoryChain
    chain = FinalStoryChain()
    assert chain is not None


def test_image_chain_init():
    """Test ImageChain can be initialized."""
    from chains.image_chain import ImageChain
    # Set CPU mode to avoid GPU requirements
    os.environ['FORCE_CPU_IMAGE'] = 'true'
    chain = ImageChain()
    assert chain is not None


def test_image_chain_handles_missing_dependencies():
    """Test ImageChain gracefully handles missing torch/diffusers."""
    from chains.image_chain import ImageChain
    # This should not raise an error even if torch/diffusers aren't installed
    chain = ImageChain()
    assert chain is not None
