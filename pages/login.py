import dash
from dash import html, dcc, Input, Output, State, callback
from flask import session

dash.register_page(__name__, path="/login", name="Login", order=0)

layout = html.Div([
    html.H1("Login"),
    
    dcc.Input(id="username", type="text", placeholder="Username", style={'margin': '10px'}),
    dcc.Input(id="password", type="password", placeholder="Password", style={'margin': '10px'}),
    
    html.Button("Log in", id="login-button"),
    html.Div(id="login-message")
])

@callback(
    Output("login-message", "children"),
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def login(n, username, password):
    # simple hard-coded login for now
    if username == "admin" and password == "flow":
        session["logged_in"] = True
        return dcc.Location(href="/dashboard", id="redirect-after-login")

    return "Invalid credentials"
