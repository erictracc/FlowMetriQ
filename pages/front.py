import dash
from dash import html, dcc

dash.register_page(__name__, path="/", title="FlowMetriQ")

layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "padding": "0",
        "margin": "0",
        "backgroundColor": "#F5F6FA"
    },
    children=[

        # ----- NAVBAR -----
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "20px 40px",
                "backgroundColor": "white",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                "position": "sticky",
                "top": "0",
                "zIndex": "1000"
            },
            children=[
                html.H2("FlowMetriQ", style={"margin": 0, "color": "#1A237E"}),

                html.Div(
                    children=[
                        html.A("Login", href="/login",
                               style={"marginLeft": "20px", "fontSize": "16px", "color": "#1A237E",
                                      "textDecoration": "none"})
                    ]
                )
            ],
        ),

        # ----- HERO SECTION -----
        html.Div(
            style={
                "padding": "100px 40px",
                "textAlign": "center",
                "background": "linear-gradient(135deg, #1A237E, #3949AB)",
                "color": "white"
            },
            children=[
                html.H1(
                    "Unlock Insights From Your Business Processes",
                    style={"fontSize": "42px", "fontWeight": "bold", "marginBottom": "20px"},
                ),
                html.P(
                    "Analyze throughput, detect bottlenecks, and enhance performance using real event logs.",
                    style={"fontSize": "20px", "opacity": "0.9"},
                ),

                html.A(
                    "Go to Login →",
                    href="/login",
                    style={
                        "display": "inline-block",
                        "marginTop": "30px",
                        "padding": "12px 28px",
                        "backgroundColor": "#FFC107",
                        "borderRadius": "6px",
                        "color": "#1A237E",
                        "fontWeight": "bold",
                        "textDecoration": "none",
                        "fontSize": "18px"
                    }
                )
            ],
        ),
    ]
)
