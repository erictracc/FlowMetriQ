from dash import Dash, html
import dash
from config_manager import load_settings

settings = load_settings()

app = Dash(__name__, use_pages=True)

# Basic temporary layout
app.layout = html.Div([
    html.H1("FlowMetriQ Dashboard"),
    html.P("If you see this, Dash is working!"),
    dash.page_container  # required when using use_pages=True
])

# Load host and port from secret settings.json
HOST = settings.get("host", "127.0.0.1")
PORT = settings.get("port", 8050)

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=True)
