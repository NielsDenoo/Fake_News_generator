import os
import uuid
import base64
import urllib.parse
import socket
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

import dash
from dash import html, dcc, Output, Input, State, no_update
import dash_bootstrap_components as dbc


def check_ollama(host_url: str, timeout: float = 2.0) -> bool:
    try:
        parsed = urllib.parse.urlparse(host_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 11434
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def create_dash_app():
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.FONT_AWESOME])

    app.layout = dbc.Container(
        [
            dcc.Store(id="session-id", data=str(uuid.uuid4())),
            
            # Header
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([html.I(className="fas fa-newspaper me-3"), "AI Fake News Generator"], 
                               className="text-center mb-2 mt-4"),
                        html.P("Generate creative fictional news stories using AI and real headlines",
                               className="text-center text-muted mb-4")
                    ])
                ], width=12)
            ]),

            # News Category Selection Card
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-cog me-2"), "Step 1: Select News Category"], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Dropdown(
                                        id="category",
                                        options=[
                                            {"label": c.title(), "value": c}
                                            for c in [
                                                "general",
                                                "business",
                                                "entertainment",
                                                "technology",
                                                "science",
                                                "sports",
                                                "health",
                                            ]
                                        ],
                                        value="general",
                                        className="mb-3",
                                        style={"color": "#000"}
                                    ),
                                ], md=8),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-download me-2"), "Load News"], 
                                        id="load-btn", 
                                        color="primary", 
                                        size="lg",
                                        className="w-100"
                                    ),
                                ], md=4),
                            ]),
                            dbc.Alert(id="status", children="", color="info", is_open=False, className="mt-3"),
                        ])
                    ], className="shadow-sm mb-4")
                ], width=12)
            ]),

            # Titles Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-list me-2"), "Step 2: Choose a Creative Title"], className="mb-3"),
                            dcc.Loading(
                                id="loading-titles",
                                type="default",
                                children=html.Div(id="titles-area")
                            )
                        ])
                    ], className="shadow-sm mb-4", id="titles-card", style={"display": "none"})
                ], width=12)
            ]),

            # Step 3 Header
            dbc.Row([
                dbc.Col([
                    html.H5([html.I(className="fas fa-route me-2"), "Step 3: Pick a Direction"], className="mb-3 mt-2"),
                ], width=12)
            ], id="step3-header", style={"display": "none"}),

            # Article and Continuations Section (side by side)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6([html.I(className="fas fa-file-alt me-2"), "Original Article"], className="mb-3"),
                            html.Div(id="article-area")
                        ])
                    ], className="shadow-sm h-100")
                ], xs=12, md=6, lg=7),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6([html.I(className="fas fa-bullseye me-2"), "Choose Direction"], className="mb-3"),
                            dcc.Loading(
                                id="loading-continuations",
                                type="default",
                                children=html.Div(id="continuations-area")
                            )
                        ])
                    ], className="shadow-sm h-100")
                ], xs=12, md=6, lg=5),
            ], className="mb-4 gx-3", id="article-row", style={"display": "none"}),

            # Final Story Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-magic me-2"), "Step 4: Generated Story & Image"], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Loading(
                                        id="loading-story",
                                        type="default",
                                        children=html.Div(id="final-story")
                                    )
                                ], md=8),
                                dbc.Col([
                                    dcc.Loading(
                                        id="loading-image",
                                        type="default",
                                        children=html.Div(id="image-area")
                                    )
                                ], md=4),
                            ])
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ], id="final-row", style={"display": "none"}),

            html.Div(id="hidden-debug", style={"display": "none"}),
            html.Div(style={"height": "50px"}),  # Bottom spacing
        ],
        fluid=True,
        className="py-4"
    )

    # Load latest news
    @app.callback(
        [Output("status", "children"), Output("titles-area", "children")],
        [Input("load-btn", "n_clicks")],
        [State("session-id", "data"), State("category", "value")],
        prevent_initial_call=True,
    )
    def on_load(n_clicks, session_id, category):
        try:
            load_latest_news(session_id, category=category)
            titles = generate_titles_for_session(session_id)
            # build title buttons
            buttons = []
            for i, t in enumerate(titles):
                btn = dbc.Button(
                    t, 
                    id={"type": "title-btn", "index": i}, 
                    color="light", 
                    outline=True,
                    className="m-2 text-start",
                    style={"whiteSpace": "normal", "height": "auto", "minHeight": "60px"},
                    n_clicks=0
                )
                buttons.append(dbc.Col(btn, md=6, lg=4))
            return dbc.Alert([html.I(className="fas fa-check-circle me-2"), "News loaded successfully! Choose a title below."], color="success", is_open=True), dbc.Row(buttons, className="g-2")
        except Exception as e:
            return dbc.Alert([html.I(className="fas fa-exclamation-triangle me-2"), f"Error: {e}"], color="danger", is_open=True), ""

    # Title selection -> show article and generate continuations
    @app.callback(
        [Output("article-area", "children", allow_duplicate=True), Output("status", "children", allow_duplicate=True), Output("continuations-area", "children", allow_duplicate=True)],
        [Input({"type": "title-btn", "index": dash.ALL}, "n_clicks")],
        [State("session-id", "data")],
        prevent_initial_call=True,
    )
    def on_select_title(n_clicks_list, session_id):
        # determine which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return no_update, no_update, no_update
        prop_id = ctx.triggered[0]["prop_id"]
        try:
            # prop_id looks like '{"type":"title-btn","index":0}.n_clicks'
            idx = int(prop_id.split('index":')[1].split('}')[0])
        except Exception:
            idx = 0
        try:
            article = select_article(session_id, idx)
            raw_content = article.content or article.description or ""
            import re

            cleaned_content = re.sub(r"\s*\[\+\d+ chars\]$", "", raw_content)
            preview = cleaned_content[:500] + ("..." if len(cleaned_content) > 500 else "")
            article_md = html.Div([
                html.H6(article.title, className="mb-3 text-primary"),
                html.P(preview, className="text-light", style={"fontSize": "0.95rem"}),
                dbc.Button(
                    [html.I(className="fas fa-external-link-alt me-2"), "Read Original"],
                    href=str(article.url),
                    target="_blank",
                    color="secondary",
                    size="sm",
                    outline=True,
                    className="mt-2"
                ),
            ])

            opts = generate_continuations_for_session(session_id)
            cbuttons = []
            for i, c in enumerate(opts):
                cb = dbc.Button(
                    c,
                    id={"type": "cont-btn", "index": i},
                    color="warning",
                    outline=True,
                    className="mb-2 w-100 text-start",
                    style={"whiteSpace": "normal", "height": "auto", "minHeight": "50px"},
                    n_clicks=0
                )
                cbuttons.append(cb)

            return article_md, dbc.Alert([html.I(className="fas fa-arrow-right me-2"), "Article selected! Pick a continuation direction."], color="info", is_open=True), html.Div(cbuttons)
        except Exception as e:
            return "", dbc.Alert([html.I(className="fas fa-exclamation-triangle me-2"), f"Error: {e}"], color="danger", is_open=True), ""

    # Continuation selection -> generate final story and image
    @app.callback(
        [Output("status", "children", allow_duplicate=True), Output("final-story", "children"), Output("image-area", "children")],
        [Input({"type": "cont-btn", "index": dash.ALL}, "n_clicks")],
        [State("session-id", "data")],
        prevent_initial_call=True,
    )
    def on_select_continuation(n_clicks_list, session_id):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return no_update, no_update, no_update
        prop_id = ctx.triggered[0]["prop_id"]
        try:
            idx = int(prop_id.split('index":')[1].split('}')[0])
        except Exception:
            idx = 0
        try:
            choice = select_continuation(session_id, idx)
            # generate final and image
            final_text, image_pil = generate_final_and_image(session_id)
            img_component = None
            if image_pil:
                # image_pil is a PIL Image object; convert to base64
                buffered = base64.b64encode(image_pil.tobytes()) if hasattr(image_pil, "tobytes") else None
                # safer: read from state.image_base64 if present
                b64 = memory.get(session_id).image_base64
                if b64:
                    img_src = f"data:image/png;base64,{b64}"
                    img_component = dbc.Card([
                        dbc.CardImg(src=img_src, top=True, style={"borderRadius": "8px"})
                    ], className="shadow-sm")
            
            story_display = dbc.Card([
                dbc.CardBody([
                    html.Div(final_text, style={"whiteSpace": "pre-wrap", "fontSize": "1rem", "lineHeight": "1.6"})
                ])
            ], className="bg-dark border-secondary")
            
            return dbc.Alert([html.I(className="fas fa-check-circle me-2"), "Story generated successfully!"], color="success", is_open=True), story_display, img_component
        except Exception as e:
            return dbc.Alert([html.I(className="fas fa-exclamation-triangle me-2"), f"Error: {e}"], color="danger", is_open=True), f"Error: {e}", ""

    # Show titles card when titles are loaded
    @app.callback(
        Output("titles-card", "style"),
        Input("titles-area", "children"),
        prevent_initial_call=True,
    )
    def show_titles_card(titles_content):
        if titles_content:
            return {"display": "block"}
        return {"display": "none"}

    # Show step 3 header and article row when continuations are loaded
    @app.callback(
        [Output("step3-header", "style"), Output("article-row", "style")],
        Input("continuations-area", "children"),
        prevent_initial_call=True,
    )
    def show_article_sections(continuations_content):
        if continuations_content:
            return {"display": "block"}, {"display": "flex"}
        return {"display": "none"}, {"display": "none"}

    # Show final row when story is generated
    @app.callback(
        Output("final-row", "style"),
        Input("final-story", "children"),
        prevent_initial_call=True,
    )
    def show_final_row(story_content):
        if story_content:
            return {"display": "block"}
        return {"display": "none"}

    return app


if __name__ == "__main__":
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if not check_ollama(ollama_base):
        print(
            "[Warning] Could not connect to Ollama at",
            ollama_base,
            "— the app may fail to generate text. Start the Ollama server with `ollama serve`, or set OLLAMA_BASE_URL to a reachable host.")

    dash_app = create_dash_app()
    # Run on port 7860 for parity with previous Gradio default
    dash_app.run(host="0.0.0.0", port=7860, debug=False)
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
