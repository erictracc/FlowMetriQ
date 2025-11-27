from dash import Dash, html, dcc
import dash
from flask import session, redirect, request
from config_manager import load_settings
from auth import check_credentials

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

    # allow public routes
    if path in PUBLIC_PATHS or path.startswith("/assets"):
        return

    # Dash pages go under /<page_name>
    # so allow the login page fully
    if path == "/login":
        return

    # Logged in?
    if not session.get("logged_in"):
        return redirect("/login")


# ---------------------------------------------------------
# Main App Layout: Must be a function for session-aware routing
# ---------------------------------------------------------
def serve_layout():
    return html.Div([
        dcc.Location(id="url"),
        dash.page_container
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
