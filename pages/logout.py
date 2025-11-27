import dash
from dash import html, dcc
from flask import session

dash.register_page(__name__, path="/logout")

layout = html.Div([
    html.H2("Logging out...")
])

@app.callback(Output("dummy", "children"), Input("dummy", "id"))
def _logout(_):
    session.pop("logged_in", None)
    return dcc.Location(href="/")
