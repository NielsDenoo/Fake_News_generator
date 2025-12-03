import os
import base64
import io
from typing import List
from PIL import Image
from tools.news_tool import NewsTool
from memory.session_memory import memory
from chains.title_chain import TitleChain
from chains.continuation_chain import ContinuationChain
from chains.final_story_chain import FinalStoryChain
from chains.image_chain import ImageChain
from schemas import Article


news_tool = NewsTool()
title_chain = TitleChain()
continuation_chain = ContinuationChain()
final_chain = FinalStoryChain()
image_chain = ImageChain()


def load_latest_news(session_id: str, category: str = "general", country: str = "us") -> List[Article]:
    # fetch and store in session
    articles = news_tool.fetch_top_headlines(category=category)
    state = memory.get(session_id)
    state.articles = articles
    state.selected_article_index = None
    state.continuation_options = []
    state.selected_continuation_index = None
    state.final_story = None
    state.image_base64 = None
    memory.set(session_id, state)
    return articles


def generate_titles_for_session(session_id: str):
    state = memory.get(session_id)
    try:
        titles_out = title_chain.generate(state.articles)
        return titles_out.titles
    except Exception as e:
        print(f"[main.py] Error in generate_titles_for_session: {e}")
        import traceback
        traceback.print_exc()
        raise


def select_article(session_id: str, index: int):
    state = memory.get(session_id)
    if not (0 <= index < len(state.articles)):
        raise IndexError("Article index out of range")
    state.selected_article_index = index
    # reset downstream data
    state.continuation_options = []
    state.selected_continuation_index = None
    state.final_story = None
    state.image_base64 = None
    memory.set(session_id, state)
    return state.articles[index]


def generate_continuations_for_session(session_id: str):
    state = memory.get(session_id)
    if state.selected_article_index is None:
        raise RuntimeError("No article selected")
    article = state.articles[state.selected_article_index]
    article_text = (article.content or article.description or article.title)[:4000]
    opts = continuation_chain.generate(article_text)
    state.continuation_options = opts.options
    memory.set(session_id, state)
    return opts.options


def select_continuation(session_id: str, index: int):
    state = memory.get(session_id)
    if not (0 <= index < len(state.continuation_options)):
        raise IndexError("Continuation index out of range")
    state.selected_continuation_index = index
    memory.set(session_id, state)
    return state.continuation_options[index]


def generate_final_and_image(session_id: str):
    state = memory.get(session_id)
    if state.selected_article_index is None or state.selected_continuation_index is None:
        raise RuntimeError("Article or continuation not selected")
    article = state.articles[state.selected_article_index]
    continuation = state.continuation_options[state.selected_continuation_index]
    final_story = final_chain.generate(article.title, article.content or article.description or article.title, continuation)
    state.final_story = final_story
    # generate image base64
    b64 = image_chain.generate(final_story)
    state.image_base64 = b64
    memory.set(session_id, state)
    # produce PIL Image for Gradio by decoding base64
    image_bytes = base64.b64decode(b64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return final_story, image


__all__ = [
    "load_latest_news",
    "generate_titles_for_session",
    "select_article",
    "generate_continuations_for_session",
    "select_continuation",
    "generate_final_and_image",
]
