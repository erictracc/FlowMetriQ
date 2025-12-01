from dash import html
import dash

def navbar():
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "12px 30px",
            "backgroundColor": "white",
            "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
            "position": "sticky",
            "top": "0",
            "zIndex": "1000",
            "fontFamily": "Arial"
        },
        children=[
            html.Div("FlowMetriQ", style={"fontSize": "22px", "fontWeight": "bold"}),

            html.Div(
                style={"display": "flex", "gap": "25px", "fontSize": "16px"},
                children=[
                    html.A("Home", href="/home", style={"textDecoration": "none", "color": "#1A237E"}),
                    html.A("Analysis", href="/analysis", style={"textDecoration": "none", "color": "#1A237E"}),
                    html.A("Prediction", href="/prediction", style={"textDecoration": "none", "color": "#1A237E"}),

                    #Simulation Tab
                    html.A("Simulation", href="/simulation", style={"textDecoration": "none", "color": "#1A237E"}),

                    html.A("Logout", href="/logout", style={"textDecoration": "none", "color": "#C62828"})
                ]
            ),
        ]
    )
