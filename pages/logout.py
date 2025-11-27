import dash
from dash import html, dcc, callback, Output, Input
from flask import session

dash.register_page(__name__, path="/logout", title="Logout")

layout = html.Div([
    dcc.Location(id="logout-trigger"),
    dcc.Location(id="logout-redirect")
])


@callback(
    Output("logout-redirect", "pathname"),
    Input("logout-trigger", "pathname"),
    prevent_initial_call=False
)
def logout_user(_):
    session.clear()
    return "/login"
