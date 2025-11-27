import dash
from dash import html, dcc, Input, Output, State, callback
from flask import session
from auth import check_credentials

dash.register_page(__name__, path="/login", title="Login")

layout = html.Div(
    style={
        "display": "flex",
        "justifyContent": "center",
        "alignItems": "center",
        "height": "100vh",
        "background": "#F0F2F5",
        "fontFamily": "Arial, sans-serif"
    },
    children=[
        html.Div(
            style={
                "width": "380px",
                "padding": "40px",
                "borderRadius": "10px",
                "backgroundColor": "white",
                "boxShadow": "0 4px 12px rgba(0,0,0,0.15)"
            },
            children=[
                html.H2("FlowMetriQ Login",
                    style={"textAlign": "center", "marginBottom": "25px", "color": "#1A237E"}),

                dcc.Input(
                    id="username",
                    type="text",
                    placeholder="Username",
                    style={
                        "width": "100%",
                        "padding": "12px",
                        "marginBottom": "15px",
                        "borderRadius": "6px",
                        "border": "1px solid #ccc",
                        "fontSize": "16px"
                    }
                ),
                dcc.Input(
                    id="password",
                    type="password",
                    placeholder="Password",
                    style={
                        "width": "100%",
                        "padding": "12px",
                        "marginBottom": "20px",
                        "borderRadius": "6px",
                        "border": "1px solid #ccc",
                        "fontSize": "16px"
                    }
                ),

                html.Button(
                    "Login",
                    id="login-button",
                    style={
                        "width": "100%",
                        "padding": "12px",
                        "backgroundColor": "#1A237E",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "fontSize": "16px",
                        "cursor": "pointer"
                    }
                ),

                html.Div(id="login-status",
                    style={"marginTop": "15px", "color": "red", "textAlign": "center"}),

                dcc.Location(id="redirect-after-login", refresh=True)
            ],
        )
    ]
)


@callback(
    Output("login-status", "children"),
    Output("redirect-after-login", "href"),
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def process_login(n_clicks, username, password):
    if not username or not password:
        return "Please fill in both fields.", dash.no_update

    if check_credentials(username, password):
        session["logged_in"] = True
        return "", "/home"

    return "Invalid username or password.", dash.no_update
