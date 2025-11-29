from dash import Dash, html, dcc
import dash
from flask import session, redirect, request
from config_manager import load_settings
from auth import check_credentials
from components.navbar import navbar
from db.mongo import get_db
from db.collections import ensure_collections

# ---------------------------------------------------------
# Load server settings
# ---------------------------------------------------------
settings = load_settings()
HOST = settings.get("host", "127.0.0.1")
PORT = settings.get("port", 8050)

# ---------------------------------------------------------
# Dash + Flask Setup
# ---------------------------------------------------------
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)

server = app.server
server.secret_key = "H39as98jhASD987nasd798ASDa98s7dASDV"  # important

# ---------------------------------------------------------
# SESSION-PERSISTENT GLOBAL STORES (created ONCE)
# ---------------------------------------------------------
global_stores = html.Div([
    dcc.Store(id="global-log-store", storage_type="session"),
    dcc.Store(id="global-log-name", storage_type="session"),
])

# ---------------------------------------------------------
# MONGO INITIALIZATION — run ONCE per process
# ---------------------------------------------------------
if not hasattr(server, "_mongo_initialized"):
    try:
        db = get_db()
        server.db = db
        print(f"[MongoDB] Connected → {settings['database_uri']} / {settings['database_name']}")

        ensure_collections(db)
        print("[MongoDB] Collections Verified")

        server._mongo_initialized = True  # prevents accidental re-runs
    except Exception as e:
        print("[MongoDB] ERROR:", str(e))
        server.db = None

# ---------------------------------------------------------
# Authentication Guard
# ---------------------------------------------------------
PUBLIC_PATHS = {
    "/",
    "/login",
    "/_dash-layout",
    "/_dash-dependencies",
    "/_dash-update-component",
}

@server.before_request
def enforce_login():
    path = request.path
    if path.startswith("/_dash"):
        return
    if path.startswith("/assets"):
        return
    if path == "/favicon.ico" or path == "/_favicon.ico":
        return
    if path == "/login":
        return
    if path == "/":
        return
    if not session.get("logged_in"):
        return redirect("/login")

# ---------------------------------------------------------
# Dynamic Layout (session-aware)
# ---------------------------------------------------------
def serve_layout():
    from flask import session as flask_session

    if not flask_session.get("logged_in"):
        return html.Div([
            global_stores,
            dcc.Location(id="url"),
            dash.page_container
        ])

    return html.Div([
        global_stores,
        navbar(),
        dcc.Location(id="url"),
        html.Div(dash.page_container, style={"padding": "20px"}),
    ])

app.layout = serve_layout

# ---------------------------------------------------------
# Run App
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=True,
        use_reloader=False  # prevents double-execution and WinError 10038
    )
