# pages/prediction.py

import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from services.log_service import load_df, list_logs
from services.prediction_service import (
    build_prediction_models,
    predict_for_case,
    build_next_event_probability_figure,
    predict_next_markov,
)

dash.register_page(__name__, path="/prediction", title="Prediction Sandbox")


# ==========================================================
# Layout
# ==========================================================
layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial"},
    children=[
        html.H2("Prediction Sandbox", style={"marginBottom": "20px"}),

        # ---------------- TOP BAR ----------------
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "flexWrap": "wrap",
                "marginBottom": "25px",
                "alignItems": "center"
            },
            children=[
                # Log selector
                html.Div(
                    style={"minWidth": "260px", "flex": "1"},
                    children=[
                        html.Label("Select Log"),
                        dcc.Dropdown(
                            id="prediction-log-selector",
                            options=[],
                            placeholder="Select loaded log",
                        ),
                    ],
                ),

                # Case selector
                html.Div(
                    style={"minWidth": "260px", "flex": "1"},
                    children=[
                        html.Label("Select Case"),
                        dcc.Dropdown(
                            id="prediction-case-selector",
                            options=[],
                            placeholder="Select a Case ID",
                        ),
                    ],
                ),

                # Run button
                html.Button(
                    "Run Predictions",
                    id="run-predictions",
                    n_clicks=0,
                    style={
                        "height": "42px",
                        "padding": "0 22px",
                        "backgroundColor": "#1976D2",
                        "color": "white",
                        "borderRadius": "6px",
                        "border": "none",
                        "cursor": "pointer",
                        "marginTop": "22px",
                    },
                ),
            ],
        ),

        html.Hr(),

        # ---------------- NEXT ACTIVITY ----------------
        html.H3("1. Next Activity Prediction"),
        html.Div(id="next-activity-text", style={"marginBottom": "10px"}),
        dcc.Graph(id="next-activity-prob-graph"),

        html.Hr(style={"margin": "30px 0"}),

        # ---------------- MARKOV CHAIN ----------------
        html.H3("1b. Markov Chain Prediction"),
        html.Div(id="markov-text", style={"marginBottom": "10px"}),

        html.Hr(style={"margin": "30px 0"}),

        # ---------------- REMAINING TIME ----------------
        html.H3("2. Remaining Time Prediction"),
        html.Div(id="remaining-time-text", style={"marginBottom": "10px"}),

        html.Hr(style={"margin": "30px 0"}),

        # ---------------- MODEL ACCURACY ----------------
        html.H3("3. Model Accuracy (80/20 Split)"),
        html.Div(id="model-metrics-text", style={"marginBottom": "10px"}),
    ],
)


# ==========================================================
# Populate Log Dropdown
# ==========================================================
@callback(
    Output("prediction-log-selector", "options"),
    Input("url", "pathname"),
)
def populate_logs(_):
    logs = list_logs()
    return [{"label": l["filename"], "value": str(l["_id"])} for l in logs]


# ==========================================================
# Populate Case Dropdown
# ==========================================================
@callback(
    Output("prediction-case-selector", "options"),
    Input("prediction-log-selector", "value"),
)
def populate_cases(log_id):

    if not log_id:
        return []

    df = load_df(log_id)
    if df is None or df.empty:
        return []

    df = df.copy()
    df["CASE ID"] = df["CASE ID"].astype(str)

    case_ids = sorted(df["CASE ID"].unique())
    return [{"label": cid, "value": cid} for cid in case_ids]


# ==========================================================
# Main Callback
# ==========================================================
@callback(
    Output("next-activity-text", "children"),
    Output("next-activity-prob-graph", "figure"),
    Output("markov-text", "children"),
    Output("remaining-time-text", "children"),
    Output("model-metrics-text", "children"),
    Input("run-predictions", "n_clicks"),
    State("prediction-log-selector", "value"),
    State("prediction-case-selector", "value"),
    prevent_initial_call=True,
)
def run_predictions(_, log_id, case_id):

    empty_fig = go.Figure()

    # No log selected
    if not log_id:
        return (
            "Please select a log first.",
            empty_fig,
            "",
            "No remaining time estimate.",
            "No metrics available."
        )

    df = load_df(log_id)
    if df is None or df.empty:
        return (
            "Log failed to load.",
            empty_fig,
            "",
            "No remaining time available.",
            "No metrics available."
        )

    # Build ML models
    models = build_prediction_models(df)
    if models is None:
        return (
            "Not enough structured data to train prediction models.",
            empty_fig,
            "",
            "No remaining time estimate.",
            "No metrics available."
        )

    # ==========================================================
    # GLOBAL METRICS
    # ==========================================================
    next_acc = models["next_acc"] * 100
    rem_mae = models["rem_mae"]
    rem_mae_baseline = models["rem_mae_baseline"]

    metrics_text = html.Div([
        html.H4("Model Overview"),

        html.Div([html.B("Next-Activity Model: "), "Random Forest Classifier"]),
        html.Div([html.I("Features: last activity, prefix length, elapsed time, time since last event")]),
        html.Br(),

        html.Div([html.B("Remaining-Time Model: "), "Gradient Boosting Regressor"]),
        html.Div([html.I("Features: prefix length, elapsed time, last-event duration, event counts")]),
        html.Br(),

        html.Div([html.B("Next-activity accuracy: "), f"{next_acc:.1f}% (80/20 split)"]),
        html.Div([html.B("Remaining-time MAE: "), f"{rem_mae:.1f} minutes (baseline: {rem_mae_baseline:.1f} minutes)"]),
    ])

    # No case selected
    if not case_id:
        return (
            "Select a case to see predictions.",
            empty_fig,
            "",
            "No remaining time available.",
            metrics_text
        )

    # ==========================================================
    # PER-CASE PREDICTIONS
    # ==========================================================
    res = predict_for_case(df, models, case_id, top_k=3)

    last_event = res["last_event"]
    next_events = res["next_events"]

    # ---------------- Next Activity (RF) ----------------
    if not next_events:
        next_text = f"No data available to predict next event for case {case_id}."
        next_fig = empty_fig
    else:
        next_text = html.Div([
            html.H4("Random Forest Prediction"),
            html.I("Features: last activity, prefix length, elapsed time, time since last event"),
            html.Br(), html.Br(),
            html.B(f"Top predictions for case {case_id}:"),
            html.Ul([
                html.Li(f"{i+1}. {item['event']} ({item['prob']*100:.1f}%)")
                for i, item in enumerate(next_events)
            ])
        ])
        next_fig = build_next_event_probability_figure(next_events)

    # ---------------- Markov Chain ----------------
    if last_event is None:
        markov_text = ""
    else:
        chain = models["markov_chain"]
        mc_preds = predict_next_markov(chain, last_event, top_k=3)

        if not mc_preds:
            markov_text = html.I("Markov Chain: No transition data for this event.")
        else:
            markov_text = html.Div([
                html.H4("Markov Chain Prediction"),
                html.I("Pure frequency-based, learned from training cases only"),
                html.Br(), html.Br(),
                html.B(f"From event '{last_event}':"),
                html.Ul([
                    html.Li(f"{i+1}. {p['event']} ({p['prob']*100:.1f}%)")
                    for i, p in enumerate(mc_preds)
                ])
            ])

    # ---------------- Remaining Time ----------------
    remaining_pred = res["remaining_pred"]
    remaining_true = res["remaining_true"]
    remaining_error = res["remaining_error"]

    if remaining_pred is None:
        remaining_text = "Not enough data to estimate remaining time."
    else:
        parts = [
            html.H4("Remaining-Time Model: Gradient Boosting"),
            html.I("Features: prefix length, elapsed time, last-event duration, event counts"),
            html.Br(), html.Br(),
            html.B(f"Estimated remaining time: {remaining_pred:.1f} minutes"),
        ]

        if remaining_true is not None:
            parts.append(
                html.P(
                    f"True remaining time: {remaining_true:.1f} minutes "
                    f"(error: {remaining_error:+.1f} minutes)"
                )
            )

        remaining_text = html.Div(parts)

    return next_text, next_fig, markov_text, remaining_text, metrics_text
