import dash
from dash import html

dash.register_page(__name__, path="/analysis", title="Analysis")

layout = html.Div([
    html.H2("Process Analysis"),
    html.P("Charts, metrics, and process summaries will go here."),
])
