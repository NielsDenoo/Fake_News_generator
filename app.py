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
            
            # Header with Session History Button
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1([html.I(className="fas fa-newspaper me-3"), "AI Fake News Generator"], 
                               className="text-center mb-2 mt-4"),
                        html.P("Generate creative fictional news stories using AI and real headlines",
                               className="text-center text-muted mb-3"),
                        html.Div([
                            dbc.Button(
                                [html.I(className="fas fa-history me-2"), "Session History"],
                                id="show-history-btn",
                                color="secondary",
                                size="sm",
                                outline=True
                            ),
                        ], className="d-flex justify-content-center mb-3")
                    ])
                ], width=12)
            ]),
            
            # Session History Panel (collapsed by default)
            dbc.Collapse(
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([html.I(className="fas fa-history me-2"), "Previous Sessions"], className="mb-0 d-inline-block"),
                        dbc.Button(
                            [html.I(className="fas fa-trash me-1"), "Clear History"],
                            id="clear-history-btn",
                            color="danger",
                            size="sm",
                            outline=True,
                            className="float-end"
                        ),
                    ]),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-history",
                            children=html.Div(id="history-area", children="Loading sessions...")
                        )
                    ])
                ], className="shadow-sm mb-4"),
                id="history-collapse",
                is_open=False
            ),

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

    # Load latest news (creates new session)
    @app.callback(
        [Output("status", "children"), Output("titles-area", "children"), Output("session-id", "data", allow_duplicate=True)],
        [Input("load-btn", "n_clicks")],
        [State("category", "value")],
        prevent_initial_call=True,
    )
    def on_load(n_clicks, category):
        # Create new session
        session_id = str(uuid.uuid4())
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
            return dbc.Alert([html.I(className="fas fa-check-circle me-2"), "News loaded successfully! Choose a title below."], color="success", is_open=True), dbc.Row(buttons, className="g-2"), session_id
        except Exception as e:
            return dbc.Alert([html.I(className="fas fa-exclamation-triangle me-2"), f"Error: {e}"], color="danger", is_open=True), "", no_update

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
        
        # Get the triggered input
        triggered_id = ctx.triggered[0]["prop_id"]
        
        # Parse the index from the triggered component
        title_idx = 0
        try:
            import json
            # Extract the ID part before .n_clicks
            id_str = triggered_id.split('.')[0]
            id_dict = json.loads(id_str)
            title_idx = id_dict.get("index", 0)
        except Exception as e:
            # Fallback: try the old method
            try:
                title_idx = int(triggered_id.split('index":')[1].split('}')[0])
            except Exception:
                title_idx = 0
        
        try:
            # Map title index to article index using the stored mapping
            state = memory.get(session_id)
            
            if title_idx < len(state.title_to_article_map):
                article_idx = state.title_to_article_map[title_idx]
            else:
                article_idx = title_idx  # fallback to direct mapping
            
            article = select_article(session_id, article_idx)
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
    
    # Toggle session history panel
    @app.callback(
        [Output("history-collapse", "is_open"), Output("history-area", "children")],
        Input("show-history-btn", "n_clicks"),
        State("history-collapse", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_history(n_clicks, is_open):
        # Toggle the collapse
        new_state = not is_open
        
        if new_state:
            # Load session history
            sessions = memory.get_all_sessions()
            
            if not sessions:
                return new_state, html.Div([
                    html.I(className="fas fa-info-circle me-2"),
                    "No previous sessions found. Generate a story to create your first session!"
                ], className="text-muted")
            
            # Create cards for each session
            session_cards = []
            for sid, info in sessions.items():
                # Determine badge color based on completion
                badge_color = "success" if info["is_complete"] else "secondary"
                badge_text = "Complete" if info["is_complete"] else "In Progress"
                
                card = dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6([
                                    html.I(className="fas fa-book me-2"),
                                    info["session_name"]
                                ], className="mb-2"),
                                html.P(info["summary"], className="text-muted small mb-2"),
                                html.P([
                                    html.I(className="fas fa-clock me-1"),
                                    f"Created: {info['created_at'][:16].replace('T', ' ')}"
                                ], className="text-muted small mb-0"),
                            ], md=8),
                            dbc.Col([
                                dbc.Badge(badge_text, color=badge_color, className="mb-2"),
                                dbc.Button(
                                    [html.I(className="fas fa-arrow-right me-2"), "Load"],
                                    id={"type": "load-session-btn", "index": sid},
                                    color="primary",
                                    size="sm",
                                    className="w-100"
                                ),
                            ], md=4, className="text-end"),
                        ])
                    ])
                ], className="mb-3")
                session_cards.append(card)
            
            return new_state, html.Div(session_cards)
        else:
            return new_state, "Click 'Session History' to view past sessions"
    
    # Load a previous session
    @app.callback(
        [
            Output("session-id", "data", allow_duplicate=True),
            Output("status", "children", allow_duplicate=True),
            Output("history-collapse", "is_open", allow_duplicate=True),
            Output("titles-area", "children", allow_duplicate=True),
            Output("article-area", "children", allow_duplicate=True),
            Output("continuations-area", "children", allow_duplicate=True),
            Output("final-story", "children", allow_duplicate=True),
            Output("image-area", "children", allow_duplicate=True),
        ],
        Input({"type": "load-session-btn", "index": dash.ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def load_previous_session(n_clicks_list):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return tuple([no_update] * 8)
        
        # Get the session ID from the triggered button
        triggered_id = ctx.triggered[0]["prop_id"]
        import json
        id_str = triggered_id.split('.')[0]
        id_dict = json.loads(id_str)
        session_id = id_dict.get("index")
        
        # Check if session exists
        state = memory.get(session_id)
        if not state or not state.articles:
            return (
                no_update,
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Session not found or expired."
                ], color="warning", is_open=True),
                no_update, no_update, no_update, no_update, no_update, no_update
            )
        
        # Rebuild UI based on session state
        # Note: We don't store titles separately, so we can't restore title buttons
        # But we can restore the selected article and continuations
        
        # 1. Titles area - empty since we don't store generated titles
        titles_content = []
        
        # 2. Article area
        article_content = ""
        if state.selected_article_index is not None and state.selected_article_index < len(state.articles):
            article = state.articles[state.selected_article_index]
            article_content = dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-newspaper me-2"),
                    article.title
                ]),
                dbc.CardBody([
                    html.P(article.description or "", className="mb-2"),
                    html.P(article.content or "", className="text-muted")
                ])
            ], className="shadow-sm")
        
        # 3. Continuations area
        cont_content = []
        if state.continuation_options:
            for idx, cont in enumerate(state.continuation_options):
                cont_content.append(
                    dbc.Button(
                        cont,
                        id={"type": "cont-btn", "index": idx},
                        color="info",
                        outline=True,
                        className="mb-2 w-100 text-start"
                    )
                )
        
        # 4. Final story
        story_content = ""
        if state.final_story:
            story_content = dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-book me-2"),
                    "Your AI-Generated Story"
                ]),
                dbc.CardBody(state.final_story)
            ], className="shadow-sm")
        
        # 5. Image area
        image_content = ""
        if state.image_base64:
            image_content = dbc.Card([
                dbc.CardBody([
                    html.Img(
                        src=f"data:image/png;base64,{state.image_base64}",
                        style={"maxWidth": "100%", "height": "auto"}
                    )
                ])
            ], className="shadow-sm")
        
        return (
            session_id,
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Loaded session: {state.session_name or 'Unnamed Session'}"
            ], color="success", is_open=True),
            False,  # Close history panel
            titles_content,
            article_content,
            cont_content,
            story_content,
            image_content
        )

    # Clear all session history
    @app.callback(
        [Output("history-area", "children", allow_duplicate=True), Output("status", "children", allow_duplicate=True)],
        Input("clear-history-btn", "n_clicks"),
        State("session-id", "data"),
        prevent_initial_call=True,
    )
    def clear_history(n_clicks, current_session_id):
        # Get all sessions except current one
        all_sessions = memory.get_all_sessions()
        cleared_count = 0
        
        for sid in list(all_sessions.keys()):
            if sid != current_session_id:
                memory._store.pop(sid, None)
                cleared_count += 1
        
        return (
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                f"Cleared {cleared_count} session(s). Current session preserved."
            ], color="info", is_open=True),
            dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Session history cleared ({cleared_count} sessions removed)"
            ], color="success", is_open=True)
        )
    
    return app


if __name__ == "__main__":
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if not check_ollama(ollama_base):
        print(
            "[Warning] Could not connect to Ollama at",
            ollama_base,
            "— the app may fail to generate text. Start the Ollama server with `ollama serve`, or set OLLAMA_BASE_URL to a reachable host.")

    dash_app = create_dash_app()
    dash_app.run(host="0.0.0.0", port=7860, debug=False)
