import os
import uuid
import base64
import gradio as gr
from dotenv import load_dotenv

# Load environment early so chains can pick up keys on import
load_dotenv()

from main import (
    load_latest_news,
    generate_titles_for_session,
    select_article,
    generate_continuations_for_session,
    select_continuation,
    generate_final_and_image,
)
from memory.session_memory import memory


def create_ui():
    with gr.Blocks(title="AI News Storyteller") as demo:
        session_id_state = gr.State(str(uuid.uuid4()))

        gr.Markdown("# AI Fake News Generator")

        with gr.Row():
            category_dropdown = gr.Dropdown(
                choices=["general", "business", "entertainment", "technology", "science", "sports", "health"],
                value="general",
                label="News Category"
            )
            load_btn = gr.Button("Load Latest News")
            status = gr.Textbox(value="", label="Status", interactive=False)

        # Title buttons (dynamic)
        with gr.Row():
            tbtn0 = gr.Button(visible=False)
            tbtn1 = gr.Button(visible=False)
            tbtn2 = gr.Button(visible=False)

        # Selected article display
        article_md = gr.Markdown("", elem_id="article_display")

        # Refresh button for continuations
        refresh_btn = gr.Button("Refresh Continuations", visible=False)

        # Continuation buttons
        with gr.Row():
            cbtn0 = gr.Button(visible=False)
            cbtn1 = gr.Button(visible=False)
            cbtn2 = gr.Button(visible=False)

        final_md = gr.Markdown("", label="Final Story")
        image_out = gr.Image(type="pil", label="Generated Image")

        # Callbacks
        def on_load(session_id: str, category: str):
            try:
                articles = load_latest_news(session_id, category=category)
                titles = generate_titles_for_session(session_id)
                # return updates for status and title buttons, hide continuation buttons
                return (
                    gr.update(value="Loaded latest news."),
                    gr.update(visible=True, value=titles[0]),
                    gr.update(visible=True, value=titles[1]),
                    gr.update(visible=True, value=titles[2]),
                    gr.update(visible=False),
                )
            except Exception as e:
                return (
                    gr.update(value=f"Error: {e}"),
                    gr.update(visible=False, value=""),
                    gr.update(visible=False, value=""),
                    gr.update(visible=False, value=""),
                    gr.update(visible=False),
                )

        # Wire load button
        load_btn.click(fn=on_load, inputs=[session_id_state, category_dropdown], outputs=[status, tbtn0, tbtn1, tbtn2, cbtn0])

        # Title selection handlers - automatically generate continuations
        def on_select_title(session_id: str, idx: int):
            try:
                article = select_article(session_id, idx)
                # Get article content and clean up NewsAPI truncation marker
                raw_content = article.content or article.description or ""
                # Remove the [+XXXX chars] truncation marker that NewsAPI adds
                import re
                cleaned_content = re.sub(r'\s*\[\+\d+ chars\]$', '', raw_content)
                
                # Get preview (first 500 chars)
                content_preview = cleaned_content[:500]
                if len(cleaned_content) > 500:
                    content_preview += "..."
                
                article_text = f"**{article.title}**\n\n{content_preview}\n\n[Open Article]({article.url})"
                
                # Automatically generate continuations
                opts = generate_continuations_for_session(session_id)
                return (
                    article_text,
                    "Select a continuation below:",
                    gr.update(visible=True),
                    gr.update(visible=True, value=opts[0]),
                    gr.update(visible=True, value=opts[1]),
                    gr.update(visible=True, value=opts[2]),
                )
            except Exception as e:
                return (
                    "",
                    f"Error: {e}",
                    gr.update(visible=False),
                    gr.update(visible=False, value=""),
                    gr.update(visible=False, value=""),
                    gr.update(visible=False, value=""),
                )

        tbtn0.click(fn=on_select_title, inputs=[session_id_state, gr.State(0)], outputs=[article_md, status, refresh_btn, cbtn0, cbtn1, cbtn2])
        tbtn1.click(fn=on_select_title, inputs=[session_id_state, gr.State(1)], outputs=[article_md, status, refresh_btn, cbtn0, cbtn1, cbtn2])
        tbtn2.click(fn=on_select_title, inputs=[session_id_state, gr.State(2)], outputs=[article_md, status, refresh_btn, cbtn0, cbtn1, cbtn2])

        # Continuation selection handlers - automatically generate final story and image
        def on_select_continuation(session_id: str, idx: int):
            try:
                choice = select_continuation(session_id, idx)
                
                # Automatically generate final story and image
                final_text, img_bytes = generate_final_and_image(session_id)
                
                return (
                    "Done! Your story is ready.",
                    final_text,
                    img_bytes,
                )
            except Exception as e:
                return (
                    f"Error: {e}",
                    f"Error: {e}",
                    None,
                )

        cbtn0.click(fn=on_select_continuation, inputs=[session_id_state, gr.State(0)], outputs=[status, final_md, image_out])
        cbtn1.click(fn=on_select_continuation, inputs=[session_id_state, gr.State(1)], outputs=[status, final_md, image_out])
        cbtn2.click(fn=on_select_continuation, inputs=[session_id_state, gr.State(2)], outputs=[status, final_md, image_out])

        # Refresh continuation handler
        def on_refresh_continuations(session_id: str):
            try:
                opts = generate_continuations_for_session(session_id)
                return (
                    "New continuations generated!",
                    gr.update(value=opts[0]),
                    gr.update(value=opts[1]),
                    gr.update(value=opts[2]),
                )
            except Exception as e:
                return (
                    f"Error: {e}",
                    gr.update(),
                    gr.update(),
                    gr.update(),
                )

        refresh_btn.click(fn=on_refresh_continuations, inputs=[session_id_state], outputs=[status, cbtn0, cbtn1, cbtn2])

    return demo


if __name__ == "__main__":
    # Before launching, check Ollama connectivity and warn early if unreachable.
    import urllib.parse
    import socket

    def check_ollama(host_url: str, timeout: float = 2.0) -> bool:
        try:
            parsed = urllib.parse.urlparse(host_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 11434
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False

    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if not check_ollama(ollama_base):
        print(
            "[Warning] Could not connect to Ollama at",
            ollama_base,
            "— the app may fail to generate text.\n"
            "Start the Ollama server with `ollama serve`, or set OLLAMA_BASE_URL to a reachable host."
        )

    create_ui().launch(server_name="0.0.0.0", share=False)
