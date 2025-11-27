import dash
from dash import html, dcc
from flask import session

dash.register_page(__name__, path="/dashboard")

layout = html.Div([
    html.H1("Welcome to the Dashboard"),
    html.P("You are logged in. All protected content goes here."),
    html.A("Log out", href="/logout")
])
