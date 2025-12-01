import dash
from dash import html, dcc

dash.register_page(__name__, path="/", title="FlowMetriQ")

layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "padding": "0",
        "margin": "0",
        "backgroundColor": "#F5F7FB"
    },
    children=[

        # ----- NAVBAR -----
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "20px 45px",
                "backgroundColor": "white",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.06)",
                "position": "sticky",
                "top": "0",
                "zIndex": "1000"
            },
            children=[
                html.H2(
                    "FlowMetriQ",
                    style={"margin": 0, "color": "#1A237E", "letterSpacing": "0.5px"}
                ),

                html.Div(
                    children=[
                        html.A(
                            "Login",
                            href="/login",
                            style={
                                "marginLeft": "20px",
                                "fontSize": "17px",
                                "color": "#1A237E",
                                "fontWeight": "bold",
                                "textDecoration": "none"
                            }
                        )
                    ]
                )
            ],
        ),

        # ----- HERO SECTION -----
        html.Div(
            style={
                "padding": "110px 40px 120px",
                "textAlign": "center",
                "background": "linear-gradient(145deg, #1A237E 0%, #3949AB 50%, #5C6BC0 100%)",
                "color": "white",
            },
            children=[
                html.H1(
                    "Visualize, Diagnose, and Optimize Your Processes",
                    style={
                        "fontSize": "48px",
                        "fontWeight": "900",
                        "marginBottom": "20px",
                        "lineHeight": "1.15"
                    }
                ),
                html.P(
                    "FlowMetriQ transforms event logs into actionable insights — from bottleneck discovery to predictive forecasting.",
                    style={
                        "fontSize": "20px",
                        "opacity": "0.92",
                        "maxWidth": "850px",
                        "margin": "0 auto",
                    }
                ),

                html.Div(
                    style={"marginTop": "40px"},
                    children=[
                        html.A(
                            "Get Started →",
                            href="/login",
                            style={
                                "display": "inline-block",
                                "padding": "14px 34px",
                                "backgroundColor": "#FFC107",
                                "borderRadius": "8px",
                                "color": "#1A237E",
                                "fontWeight": "bold",
                                "fontSize": "20px",
                                "textDecoration": "none",
                                "transition": "0.25s",
                            }
                        ),
                    ]
                )
            ],
        ),

        # ----- FEATURES SECTION -----
        html.Div(
            style={
                "padding": "80px 40px",
                "textAlign": "center",
                "backgroundColor": "#F5F7FB"
            },
            children=[
                html.H2(
                    "Why FlowMetriQ?",
                    style={
                        "fontSize": "34px",
                        "fontWeight": "800",
                        "color": "#1A237E",
                        "marginBottom": "50px",
                    }
                ),

                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "flexWrap": "wrap",
                        "gap": "40px",
                    },
                    children=[

                        # Feature 1
                        html.Div(
                            style={
                                "width": "280px",
                                "padding": "25px",
                                "backgroundColor": "white",
                                "borderRadius": "10px",
                                "boxShadow": "0 2px 10px rgba(0,0,0,0.08)",
                            },
                            children=[
                                html.H3("Process Discovery", style={"color": "#1A237E"}),
                                html.P("Generate flow maps and uncover hidden inefficiencies.")
                            ]
                        ),

                        # Feature 2
                        html.Div(
                            style={
                                "width": "280px",
                                "padding": "25px",
                                "backgroundColor": "white",
                                "borderRadius": "10px",
                                "boxShadow": "0 2px 10px rgba(0,0,0,0.08)",
                            },
                            children=[
                                html.H3("Bottleneck Detection", style={"color": "#1A237E"}),
                                html.P("Instantly identify long-running steps and delays.")
                            ]
                        ),

                        # Feature 3
                        html.Div(
                            style={
                                "width": "280px",
                                "padding": "25px",
                                "backgroundColor": "white",
                                "borderRadius": "10px",
                                "boxShadow": "0 2px 10px rgba(0,0,0,0.08)",
                            },
                            children=[
                                html.H3("Predictive Models", style={"color": "#1A237E"}),
                                html.P("Forecast next steps and remaining process time.")
                            ]
                        ),
                    ]
                )
            ],
        ),
    ]
)
