# pages/prediction.py

import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd  # needed for slicing/concat

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
                "alignItems": "center",
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
                            value=None,
                            clearable=True,
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
                            value=None,
                            clearable=True,
                        ),
                    ],
                ),

                # Start-from-event selector (hypothetical prefix cut)
                html.Div(
                    style={"minWidth": "320px", "flex": "1"},
                    children=[
                        html.Label("Start Prediction From (Optional)"),
                        dcc.Dropdown(
                            id="prediction-start-event",
                            options=[],
                            placeholder="Use last event in case (default)",
                            value=None,
                            clearable=True,
                        ),
                        html.Div(
                            "Pick an event position to predict from a hypothetical point in the case.",
                            style={
                                "fontSize": "12px",
                                "opacity": 0.7,
                                "marginTop": "6px",
                            },
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
# Populate Case Dropdown (only)
# ==========================================================
@callback(
    Output("prediction-case-selector", "options"),
    Output("prediction-case-selector", "value"),
    Input("prediction-log-selector", "value"),
)
def populate_cases(log_id):
    # Reset everything if no log
    if not log_id:
        return [], None

    df = load_df(log_id)
    if df is None or df.empty or "CASE ID" not in df.columns:
        return [], None

    df = df.copy()
    df["CASE ID"] = df["CASE ID"].astype(str)

    case_ids = sorted(df["CASE ID"].unique())
    case_options = [{"label": cid, "value": cid} for cid in case_ids]

    # Do not auto-select a case; user picks
    return case_options, None


# ==========================================================
# Populate "Start Prediction From" dropdown (per case)
# Values are indices (0..n-1) so we know where to hypothetically cut the trace
# ==========================================================
@callback(
    Output("prediction-start-event", "options"),
    Output("prediction-start-event", "value"),
    Input("prediction-log-selector", "value"),
    Input("prediction-case-selector", "value"),
)
def populate_start_events(log_id, case_id):
    if not log_id or not case_id:
        return [], None

    df = load_df(log_id)
    if df is None or df.empty:
        return [], None

    if "CASE ID" not in df.columns or "EVENT" not in df.columns:
        return [], None

    df = df.copy()
    df["CASE ID"] = df["CASE ID"].astype(str)
    case_df = df[df["CASE ID"] == str(case_id)]

    # Prefer START TIME order if present
    if "START TIME" in case_df.columns:
        case_df = case_df.sort_values("START TIME")

    events = case_df["EVENT"].astype(str).tolist()
    if not events:
        return [], None

    options = [
        {"label": f"{i + 1}. {evt}", "value": i}
        for i, evt in enumerate(events)
    ]

    # Default: None -> "use last event in case" (original behavior)
    return options, None


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
    State("prediction-start-event", "value"),  # index in the case (0..n-1) or None
    prevent_initial_call=True,
)
def run_predictions(_, log_id, case_id, start_index):
    empty_fig = go.Figure()

    # No log selected
    if not log_id:
        return (
            "Please select a log first.",
            empty_fig,
            "",
            "No remaining time estimate.",
            "No metrics available.",
        )

    df = load_df(log_id)
    if df is None or df.empty:
        return (
            "Log failed to load.",
            empty_fig,
            "",
            "No remaining time available.",
            "No metrics available.",
        )

    # Build ML models (train/test split happens inside)
    models = build_prediction_models(df)
    if models is None:
        return (
            "Not enough structured data to train prediction models.",
            empty_fig,
            "",
            "No remaining time estimate.",
            "No metrics available.",
        )

    # ==========================================================
    # GLOBAL METRICS
    # ==========================================================
    next_acc = float(models.get("next_acc", 0.0)) * 100.0
    rem_mae = models.get("rem_mae", None)
    rem_mae_baseline = models.get("rem_mae_baseline", None)

    metrics_bits = [
        html.H4("Model Overview"),
        html.Div([html.B("Next-Activity Model: "), "Random Forest Classifier"]),
        html.Div(
            [
                html.I(
                    "Features: last activity, prefix length, elapsed time, time since last event"
                )
            ]
        ),
        html.Br(),
        html.Div(
            [html.B("Remaining-Time Model: "), "Gradient Boosting Regressor"]
        ),
        html.Div(
            [
                html.I(
                    "Features: prefix length, elapsed time, last-event duration, event counts"
                )
            ]
        ),
        html.Br(),
        html.Div(
            [
                html.B("Next-activity accuracy: "),
                f"{next_acc:.1f}% (80/20 split)",
            ]
        ),
    ]

    if rem_mae is not None and rem_mae_baseline is not None:
        metrics_bits.append(
            html.Div(
                [
                    html.B("Remaining-time MAE: "),
                    f"{rem_mae:.1f} minutes (baseline: {rem_mae_baseline:.1f} minutes)",
                ]
            )
        )

    metrics_text = html.Div(metrics_bits)

    # No case selected
    if not case_id:
        return (
            "Select a case to see predictions.",
            empty_fig,
            "",
            "No remaining time available.",
            metrics_text,
        )

    # ==========================================================
    # Build a hypothetical prefix if start_index is chosen
    # ==========================================================
    df_for_case = df
    predicted_from_label = "(Start: last event in case)"

    if start_index is not None:
        df_local = df.copy()
        df_local["CASE ID"] = df_local["CASE ID"].astype(str)
        case_df = df_local[df_local["CASE ID"] == str(case_id)]

        if "START TIME" in case_df.columns:
            case_df = case_df.sort_values("START TIME")

        case_len = len(case_df)

        if case_len > 0 and 0 <= int(start_index) < case_len:
            # Take only prefix up to selected event index (inclusive)
            prefix = case_df.iloc[: int(start_index) + 1]

            others = df_local[df_local["CASE ID"] != str(case_id)]
            df_for_case = pd.concat([others, prefix], ignore_index=True)

            predicted_from_label = (
                f"(Hypothetical start: event #{int(start_index) + 1})"
            )
        else:
            # Invalid index, fall back to full case
            predicted_from_label = "(Start: last event in case)"

    # ==========================================================
    # PER-CASE PREDICTIONS (using possibly truncated df_for_case)
    # ==========================================================
    res = predict_for_case(df_for_case, models, case_id, top_k=3)

    last_event = res.get("last_event", None)
    next_events = res.get("next_events", [])

    # ---------------- Next Activity (RF) ----------------
    if not next_events:
        next_text = (
            f"No data available to predict next event for case {case_id}. "
            f"{predicted_from_label}"
        )
        next_fig = empty_fig
    else:
        next_text = html.Div(
            [
                html.H4("Random Forest Prediction"),
                html.I(
                    "Features: last activity, prefix length, elapsed time, time since last event"
                ),
                html.Br(),
                html.Br(),
                html.Div([html.B("Prediction point: "), predicted_from_label]),
                html.Br(),
                html.B(f"Top predictions for case {case_id}:"),
                html.Ul(
                    [
                        html.Li(
                            f"{i + 1}. {item['event']} ({item['prob']*100:.1f}%)"
                        )
                        for i, item in enumerate(next_events)
                    ]
                ),
            ]
        )
        next_fig = build_next_event_probability_figure(next_events)

    # ---------------- Markov Chain ----------------
    if last_event is None:
        markov_text = ""
    else:
        chain = models.get("markov_chain")
        mc_preds = (
            predict_next_markov(chain, last_event, top_k=3) if chain else []
        )

        if not mc_preds:
            markov_text = html.I(
                "Markov Chain: No transition data for this event."
            )
        else:
            markov_text = html.Div(
                [
                    html.H4("Markov Chain Prediction"),
                    html.I(
                        "Pure frequency-based, learned from training cases only"
                    ),
                    html.Br(),
                    html.Br(),
                    html.Div(
                        [html.B("Prediction point: "), predicted_from_label]
                    ),
                    html.Br(),
                    html.B(f"From event '{last_event}':"),
                    html.Ul(
                        [
                            html.Li(
                                f"{i + 1}. {p['event']} ({p['prob']*100:.1f}%)"
                            )
                            for i, p in enumerate(mc_preds)
                        ]
                    ),
                ]
            )

    # ---------------- Remaining Time ----------------
    remaining_pred = res.get("remaining_pred", None)
    remaining_true = res.get("remaining_true", None)
    remaining_error = res.get("remaining_error", None)

    # If we picked a hypothetical prefix, the "true remaining time" is not meaningful.
    hypothetical = start_index is not None

    if remaining_pred is None:
        remaining_text = html.Div(
            [
                html.Div([html.B("Prediction point: "), predicted_from_label]),
                html.Br(),
                "Not enough data to estimate remaining time.",
            ]
        )
    else:
        parts = [
            html.H4("Remaining-Time Model: Gradient Boosting"),
            html.I(
                "Features: prefix length, elapsed time, last-event duration, event counts"
            ),
            html.Br(),
            html.Br(),
            html.Div([html.B("Prediction point: "), predicted_from_label]),
            html.Br(),
            html.B(f"Estimated remaining time: {remaining_pred:.1f} minutes"),
        ]

        # Only show true remaining time if we used the real full trace
        if not hypothetical and remaining_true is not None and remaining_error is not None:
            parts.append(
                html.P(
                    f"True remaining time: {remaining_true:.1f} minutes "
                    f"(error: {remaining_error:+.1f} minutes)"
                )
            )

        remaining_text = html.Div(parts)

    return next_text, next_fig, markov_text, remaining_text, metrics_text
