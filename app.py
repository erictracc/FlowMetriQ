from dash import Dash, html, dcc
import dash
from flask import session, redirect, request
from config_manager import load_settings
from auth import check_credentials
from components.navbar import navbar

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
server.secret_key = "H39as98jhASD987nasd798ASDa98s7dASDV"  # IMPORTANT

# ---------------------------------------------------------
# Global Server-Side Log Store
# ---------------------------------------------------------
server.LOG_STORE = {}

# ---------------------------------------------------------
# SESSION-PERSISTENT GLOBAL STORES (created ONCE)
# ---------------------------------------------------------
global_stores = html.Div([
    dcc.Store(id="global-log-store", storage_type="session"),
    dcc.Store(id="global-log-name", storage_type="session"),
])

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

    # Allow public routes
    if path in PUBLIC_PATHS or path.startswith("/assets"):
        return

    # Allow login page
    if path == "/login":
        return

    # Block everything else unless logged in
    if not session.get("logged_in"):
        return redirect("/login")

# ---------------------------------------------------------
# Dynamic Layout (session-aware)
# ---------------------------------------------------------
def serve_layout():
    from flask import session

    # Not logged in → no navbar
    if not session.get("logged_in"):
        return html.Div([
            global_stores,
            dcc.Location(id="url"),
            dash.page_container
        ])

    # Logged in → show navbar + pages
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
        debug=True
    )
