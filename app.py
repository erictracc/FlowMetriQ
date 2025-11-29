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

    # allow login page
    if path == "/login":
        return

    # enforce login for all others
    if not session.get("logged_in"):
        return redirect("/login")


# ---------------------------------------------------------
# Main App Layout (dynamic for session-aware navbar)
# ---------------------------------------------------------
def serve_layout():
    from flask import session

    # Always include the global stores
    stores = [
        dcc.Store(id="global-log-store", storage_type="session"),
        dcc.Store(id="global-log-name", storage_type="session"),
    ]

    # If NOT logged in: no navbar, just the pages (login / front)
    if not session.get("logged_in"):
        return html.Div(
            stores + [
                dcc.Location(id="url"),
                dash.page_container
            ]
        )

    # If logged in: add navbar + pages
    return html.Div(
        stores + [
            navbar(),
            dcc.Location(id="url"),
            html.Div(dash.page_container, style={"padding": "20px"})
        ]
    )


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
