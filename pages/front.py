import dash
from dash import html

dash.register_page(__name__, path="/")

layout = html.Div([
    html.H1("FlowMetriQ"),
    html.P("Your process analytics dashboard."),
    html.A("Login →", href="/login")
])
