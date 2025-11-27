from dash import Dash, html, dcc, page_container
import dash
from flask import session, redirect, request
from config_manager import load_settings

# ---------------------------------------------------------
# Load server settings (host, port, db later, etc.)
# ---------------------------------------------------------
settings = load_settings()
HOST = settings.get("host", "127.0.0.1")
PORT = settings.get("port", 8050)

# ---------------------------------------------------------
# Hard-coded login credentials for now
# (You can move these into settings.json later)
# ---------------------------------------------------------
VALID_USERNAME = "admin"
VALID_PASSWORD = "flowmetriq"

# ---------------------------------------------------------
# Dash + Flask Setup
# ---------------------------------------------------------
app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)

server = app.server
server.secret_key = "H39as98jhASD987nasd798ASDa98s7dASDV"   # IMPORTANT

# ---------------------------------------------------------
# Root layout
# ---------------------------------------------------------
app.layout = html.Div([
    dcc.Location(id="url"),
    page_container
])

# ---------------------------------------------------------
# Authentication Guard
# ---------------------------------------------------------
PUBLIC_ROUTES = {"/", "/login", "/_dash-update-component", "/_dash-layout"}

@server.before_request
def protect_pages():
    path = request.path

    # allow public pages
    if path in PUBLIC_ROUTES or path.startswith("/assets"):
        return

    # block everything else unless logged in
    if not session.get("logged_in"):
        return redirect("/login")


# ---------------------------------------------------------
# Helper function used by login page
# ---------------------------------------------------------
def check_credentials(username, password):
    return username == VALID_USERNAME and password == VALID_PASSWORD


# ---------------------------------------------------------
# Run App
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(
        host=HOST,
        port=PORT,
        debug=True
    )
