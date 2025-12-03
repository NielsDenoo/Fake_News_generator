import os
import time
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
        # If generation fails (e.g. Ollama unreachable), fall back to lightweight heuristics
        print(f"[main.py] Error in generate_titles_for_session: {e}")
        import traceback
        traceback.print_exc()
        # Produce three short fallback titles based on article titles/descriptions
        fallback = []
        for idx, a in enumerate(state.articles[:3]):
            base = (a.title or a.description or f"Story {idx+1}")[:80]
            if idx == 0:
                fallback.append(f"Inside: {base}")
            elif idx == 1:
                fallback.append(f"What This Means: {base}")
            else:
                fallback.append(f"Spotlight — {base}")
        # If fewer than 3 articles, pad with generic items
        i = 0
        while len(fallback) < 3:
            fallback.append(f"Breaking: More to come ({len(fallback)+1})")
            i += 1
        return fallback


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
    # Retry logic with exponential backoff
    max_retries = int(os.getenv("GEN_MAX_RETRIES", "3"))
    backoff = float(os.getenv("GEN_BACKOFF", "1.0"))
    enable_fallback = os.getenv("ENABLE_FALLBACK", "false").lower() in ("1", "true", "yes")
    last_exc = None
    print(f"[PROGRESS] Starting continuation generation (max {max_retries} attempts)...")
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[PROGRESS] Continuation attempt {attempt}/{max_retries} - calling LLM...")
            opts = continuation_chain.generate(article_text)
            print(f"[PROGRESS] ✓ Continuation generation complete")
            state.continuation_options = opts.options
            memory.set(session_id, state)
            return opts.options
        except Exception as e:
            last_exc = e
            print(f"[main.py] continuation attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            # last attempt failed
    # After retries exhausted
    import traceback
    traceback.print_exc()
    if enable_fallback:
        fallback_opts = [
            "A surprising political scandal develops around the story.",
            "A human-interest angle focusing on an unlikely hero.",
            "A conspiracy-style twist that reinterprets the events dramatically.",
        ]
        state.continuation_options = fallback_opts
        memory.set(session_id, state)
        return fallback_opts
    # Fallback disabled — propagate the last exception so caller (UI) can show an error
    raise last_exc


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
    # Retry final story generation
    max_retries = int(os.getenv("GEN_MAX_RETRIES", "3"))
    backoff = float(os.getenv("GEN_BACKOFF", "1.0"))
    enable_fallback = os.getenv("ENABLE_FALLBACK", "false").lower() in ("1", "true", "yes")
    last_exc = None
    final_story = None
    print(f"[PROGRESS] Starting final story generation (max {max_retries} attempts)...")
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[PROGRESS] Final story attempt {attempt}/{max_retries} - calling LLM...")
            final_story = final_chain.generate(article.title, article.content or article.description or article.title, continuation)
            print(f"[PROGRESS] ✓ Final story generation complete")
            state.final_story = final_story
            memory.set(session_id, state)
            break
        except Exception as e:
            last_exc = e
            print(f"[main.py] final generation attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
    if final_story is None:
        import traceback
        traceback.print_exc()
        if not enable_fallback:
            raise last_exc
        # Fallback final story when disabled
        src_text = article.content or article.description or article.title or ""
        paragraph = (src_text[:600] + "...") if len(src_text) > 600 else src_text
        fallback_story = (
            f"[Fallback story — generation service unavailable]\n\n"
            f"Article: {article.title}\n\n"
            f"Summary: {paragraph}\n\n"
            f"Continuation idea used: {continuation}\n\n"
            "Story:\n"
            "In a world where details are thin, local sources tell a strange tale: "
            f"{continuation}. The original reporting suggests that "
            f"{(article.title or '').strip()} may be only part of the picture."
        )
        state.final_story = fallback_story
        state.image_base64 = None
        memory.set(session_id, state)
        return fallback_story, None

    # If we have a final story, try to generate an image (with retries)
    last_img_exc = None
    b64 = None
    backoff = float(os.getenv("GEN_BACKOFF", "1.0"))
    print(f"[PROGRESS] Starting image generation (max {max_retries} attempts)...")
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[PROGRESS] Image generation attempt {attempt}/{max_retries} - extracting prompt and generating...")
            b64 = image_chain.generate(final_story)
            print(f"[PROGRESS] ✓ Image generation complete")
            state.image_base64 = b64
            memory.set(session_id, state)
            break
        except Exception as e:
            last_img_exc = e
            print(f"[main.py] image generation attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
    if b64:
        # produce PIL Image for Gradio by decoding base64
        image_bytes = base64.b64decode(b64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return final_story, image
    # image generation failed after retries
    import traceback
    traceback.print_exc()
    if not enable_fallback:
        raise last_img_exc
    # Fallback: return final_story and no image (caller should handle None)
    state.image_base64 = None
    memory.set(session_id, state)
    return final_story, None


__all__ = [
    "load_latest_news",
    "generate_titles_for_session",
    "select_article",
    "generate_continuations_for_session",
    "select_continuation",
    "generate_final_and_image",
]
