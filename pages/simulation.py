import dash
from dash import html, dcc, dash_table, callback, Input, Output, State, no_update
import pandas as pd
import plotly.graph_objects as go
import base64, io

from components.navbar import navbar
from services.log_service import load_df, list_logs, save_log
from services.simulation_service import (
    extract_baseline_distributions,
    compute_activity_stats,
    apply_interventions,
    build_markov_chain,
    run_simulation,
)

dash.register_page(__name__, path="/simulation", name="Simulation")

# =====================================================================
# PAGE LAYOUT
# =====================================================================
layout = html.Div(
    style={"fontFamily": "Arial", "backgroundColor": "#FAFAFA"},
    children=[

        html.Div(
            style={
                "maxWidth": "1100px",
                "margin": "0 auto",
                "padding": "40px 20px"
            },
            children=[
                html.H2(
                    "Process Simulation & Activity Analyzer",
                    style={"marginBottom": "25px", "fontWeight": "600"}
                ),

                # ============================================================
                # Log Selector + Upload
                # ============================================================
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                        "marginBottom": "30px"
                    },
                    children=[
                        html.H4("Select or Upload Event Log", style={"marginBottom": "15px"}),

                        html.Label("Choose Existing Log", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="simulation-log-selector",
                            options=[],
                            placeholder="Select a loaded log",
                            style={"width": "350px", "marginBottom": "20px"}
                        ),

                        html.Div("OR", style={
                            "textAlign": "center",
                            "marginBottom": "15px",
                            "fontWeight": "bold",
                            "color": "#555"
                        }),

                        dcc.Upload(
                            id="simulation-upload",
                            children=html.Div([
                                "Drag and Drop or ",
                                html.A("Select a CSV File",
                                       style={"color": "#1A237E", "fontWeight": "bold"})
                            ]),
                            style={
                                "width": "100%",
                                "height": "65px",
                                "lineHeight": "65px",
                                "borderWidth": "2px",
                                "borderStyle": "dashed",
                                "borderRadius": "6px",
                                "textAlign": "center",
                                "backgroundColor": "#F4F6FA",
                                "cursor": "pointer"
                            },
                            multiple=False
                        ),

                        html.Button(
                            "Load Log",
                            id="load-simulation-log-btn",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#1A237E",
                                "color": "white",
                                "padding": "8px 18px",
                                "border": "none",
                                "borderRadius": "6px",
                                "cursor": "pointer",
                                "marginTop": "20px"
                            }
                        ),

                        dcc.Store(id="simulation-log-store", storage_type="session"),
                    ]
                ),

                # ============================================================
                # Activity Statistics Table
                # ============================================================
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "20px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                        "marginBottom": "35px"
                    },
                    children=[
                        html.H4("Activity Statistics", style={"marginBottom": "10px"}),
                        html.P(
                            "Baseline performance metrics per activity, computed from your event log.",
                            style={"color": "gray", "marginBottom": "20px"}
                        ),
                        dash_table.DataTable(
                            id="activity-stats-table",
                            columns=[
                                {"name": "Activity", "id": "activity"},
                                {"name": "Contribution (hrs)", "id": "contribution"},
                                {"name": "Cases", "id": "cases"},
                                {"name": "Median (hrs)", "id": "median"},
                                {"name": "Average (hrs)", "id": "mean"},
                                {"name": "90th Percentile (hrs)", "id": "p90"},
                            ],
                            data=[],
                            page_size=10,
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "center", "padding": "8px"},
                            style_header={
                                "fontWeight": "bold",
                                "backgroundColor": "#E3EAFD"
                            },
                        )
                    ]
                ),

                # ============================================================
                # Interventions Panel
                # ============================================================
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "25px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)",
                        "marginBottom": "35px"
                    },
                    children=[
                        html.H4("Modify Activity Durations (Interventions)",
                                style={"marginBottom": "10px"}),

                        html.P(
                            "Choose an activity and apply one of the following effects:",
                            style={"color": "gray", "marginBottom": "5px"}
                        ),

                        html.Ul(style={"color": "gray"}, children=[
                            html.Li("Deterministic: fixed duration (HH:MM:SS)"),
                            html.Li("Speedup: 0.20 = 20% faster"),
                            html.Li("Slowdown: 0.30 = 30% slower")
                        ]),

                        dcc.Store(id="interventions-store", storage_type="session"),

                        html.Label("Select Activity", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="intervention-activity-dropdown",
                            options=[],
                            placeholder="Select an activity",
                            style={"width": "350px", "marginBottom": "20px"}
                        ),

                        html.Label("Intervention Type", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="intervention-type-dropdown",
                            options=[
                                {"label": "Deterministic (fixed)", "value": "DETERMINISTIC"},
                                {"label": "Speedup (shorter)", "value": "SPEEDUP"},
                                {"label": "Slowdown (longer)", "value": "SLOWDOWN"},
                            ],
                            placeholder="Choose intervention type",
                            style={"width": "450px", "marginBottom": "20px"}
                        ),

                        html.Div(id="intervention-value-container"),

                        html.Button(
                            "Save Intervention",
                            id="save-intervention-btn",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#1A237E",
                                "color": "white",
                                "padding": "10px 22px",
                                "border": "none",
                                "borderRadius": "6px",
                                "cursor": "pointer",
                                "fontWeight": "600",
                                "marginTop": "10px",
                                "marginBottom": "10px"
                            }
                        ),

                        html.Div(id="intervention-feedback", style={"color": "#444"}),
                    ]
                ),

                # ============================================================
                # Simulation Results
                # ============================================================
                html.Div(
                    style={
                        "backgroundColor": "white",
                        "padding": "25px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.08)"
                    },
                    children=[
                        html.H4("Simulation Results", style={"marginBottom": "10px"}),

                        html.Div(
                            style={
                                "backgroundColor": "#F5F5F5",
                                "padding": "15px",
                                "borderRadius": "6px",
                                "marginBottom": "20px"
                            },
                            children=[
                                html.H5("How This Simulation Works", style={"marginBottom": "8px"}),
                                html.Ul(style={"color": "#555"}, children=[
                                    html.Li("Markov-chain routing model"),
                                    html.Li("Baseline duration distributions learned from log"),
                                    html.Li("Interventions modify distributions"),
                                    html.Li("Monte-Carlo simulation generates new synthetic cases"),
                                    html.Li("Compare baseline vs simulated case durations"),
                                ])
                            ]
                        ),

                        html.Button(
                            "Run Simulation",
                            id="run-simulation-btn",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#2E7D32",
                                "color": "white",
                                "padding": "10px 22px",
                                "border": "none",
                                "borderRadius": "6px",
                                "cursor": "pointer",
                                "fontWeight": "600",
                                "marginBottom": "20px"
                            }
                        ),

                        html.Div(id="simulation-results")
                    ]
                ),
            ]
        )
    ]
)

# =====================================================================
# CALLBACKS
# =====================================================================

# Populate dropdown from Mongo
@callback(
    Output("simulation-log-selector", "options"),
    Input("url", "pathname")
)
def populate_simulation_logs(_):
    logs = list_logs()
    return [{"label": l["filename"], "value": str(l["_id"])} for l in logs]


# ============================================================
# Load selected or uploaded log  (PATCHED)
# ============================================================
@callback(
    Output("simulation-log-store", "data"),
    Output("global-log-store", "data", allow_duplicate=True),
    Input("load-simulation-log-btn", "n_clicks"),
    State("simulation-log-selector", "value"),
    State("simulation-upload", "contents"),
    State("simulation-upload", "filename"),
    prevent_initial_call=True
)
def load_simulation_log(_, selected_log_id, contents, filename):

    # CASE 1 — selected existing log
    if selected_log_id:
        # Get filename from DB via list_logs (upload filename state may be None)
        fname = None
        for doc in list_logs():
            if str(doc["_id"]) == selected_log_id:
                fname = doc.get("filename")
                break

        return (
            {"log_id": selected_log_id},
            {"log_id": selected_log_id, "filename": fname}
        )

    # CASE 2 — uploaded CSV
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            new_id = save_log(df, filename)

            return (
                {"log_id": new_id},
                {"log_id": new_id, "filename": filename}
            )
        except Exception as e:
            print("[simulation] CSV upload error:", e)
            return no_update, no_update

    return no_update, no_update


# ============================================================
# Activity table + dropdown  (EVENT_DURATION patched)
# ============================================================
@callback(
    Output("activity-stats-table", "data"),
    Output("intervention-activity-dropdown", "options"),
    Input("simulation-log-store", "data")
)
def update_simulation_view(store):

    if not store:
        return [], []

    df = load_df(store["log_id"])
    if df is None or df.empty:
        return [], []

    df_sim = df.copy()

    # Normalize activity / case IDs
    if "EVENT" in df_sim.columns and "ACTIVITY" not in df_sim.columns:
        df_sim["ACTIVITY"] = df_sim["EVENT"]
    if "CASE ID" in df_sim.columns and "CASE_ID" not in df_sim.columns:
        df_sim["CASE_ID"] = df_sim["CASE ID"]

    # Ensure EVENT_DURATION exists (minutes)
    if "START TIME" in df_sim.columns and "END TIME" in df_sim.columns:
        df_sim["START TIME"] = pd.to_datetime(df_sim["START TIME"], errors="coerce")
        df_sim["END TIME"] = pd.to_datetime(df_sim["END TIME"], errors="coerce")
        df_sim["EVENT_DURATION"] = (
            df_sim["END TIME"] - df_sim["START TIME"]
        ).dt.total_seconds() / 60.0
    elif "EVENT_DURATION" not in df_sim.columns:
        df_sim["EVENT_DURATION"] = pd.NA

    stats = compute_activity_stats(df_sim)
    options = [{"label": s["activity"], "value": s["activity"]} for s in stats]

    return stats, options


# ============================================================
# Dynamic intervention input
# ============================================================
@callback(
    Output("intervention-value-container", "children"),
    Input("intervention-type-dropdown", "value"),
)
def show_intervention_input(selected_type):

    if not selected_type:
        return html.Div()

    base_input_style = {
        "width": "260px",
        "padding": "8px",
        "border": "1px solid #B0BEC5",
        "borderRadius": "6px",
        "fontSize": "15px",
        "marginTop": "5px",
        "fontFamily": "Arial",
    }

    if selected_type == "DETERMINISTIC":
        return html.Div([
            html.Label("Fixed Duration (HH:MM:SS)", style={"fontWeight": "bold"}),
            dcc.Input(
                id="intervention-value-input",
                type="text",
                placeholder="00:30:00",
                style=base_input_style
            )
        ])

    return html.Div([
        html.Label("Percentage (0 to 1)", style={"fontWeight": "bold"}),
        dcc.Input(
            id="intervention-value-input",
            type="number",
            min=0,
            max=1,
            step=0.05,
            placeholder="0.20 for 20%",
            style=base_input_style
        )
    ])


# ============================================================
# Save intervention
# ============================================================
@callback(
    Output("interventions-store", "data", allow_duplicate=True),
    Output("intervention-feedback", "children", allow_duplicate=True),
    Input("save-intervention-btn", "n_clicks"),
    State("intervention-activity-dropdown", "value"),
    State("intervention-type-dropdown", "value"),
    State("intervention-value-input", "value"),
    State("interventions-store", "data"),
    prevent_initial_call=True
)
def save_intervention(_, activity, inter_type, value, store):

    if not activity or not inter_type or value in (None, ""):
        return store, " Please fill all fields."

    if store is None:
        store = {}

    store[activity] = {"type": inter_type, "value": value}

    return store, f" Successfully saved intervention for {activity}: {inter_type} ({value})"


# ============================================================
# Run simulation  (EVENT_DURATION patched)
# ============================================================
@callback(
    Output("simulation-results", "children"),
    Input("run-simulation-btn", "n_clicks"),
    State("simulation-log-store", "data"),
    State("interventions-store", "data"),
    prevent_initial_call=True
)
def run_full_simulation(_, store, interventions):

    if not store:
        return " No log loaded."

    df = load_df(store["log_id"])
    if df is None or df.empty:
        return " Invalid log."

    df_sim = df.copy()

    # Normalize
    if "EVENT" in df_sim.columns and "ACTIVITY" not in df_sim.columns:
        df_sim["ACTIVITY"] = df_sim["EVENT"]
    if "CASE ID" in df_sim.columns and "CASE_ID" not in df_sim.columns:
        df_sim["CASE_ID"] = df_sim["CASE ID"]

    # Ensure EVENT_DURATION exists (minutes)
    if "START TIME" in df_sim.columns and "END TIME" in df_sim.columns:
        df_sim["START TIME"] = pd.to_datetime(df_sim["START TIME"], errors="coerce")
        df_sim["END TIME"] = pd.to_datetime(df_sim["END TIME"], errors="coerce")
        df_sim["EVENT_DURATION"] = (
            df_sim["END TIME"] - df_sim["START TIME"]
        ).dt.total_seconds() / 60.0
    elif "EVENT_DURATION" not in df_sim.columns:
        df_sim["EVENT_DURATION"] = pd.NA

    # Baseline distributions + Markov chain
    baseline_dists = extract_baseline_distributions(df_sim)
    markov = build_markov_chain(df_sim)

    if interventions is None:
        interventions = {}

    modified_dists = apply_interventions(baseline_dists, interventions)

    sim_results = run_simulation(
        markov, modified_dists, df_sim,
        n_cases=200, iterations=3
    )

    sim_case_durations = []
    for iteration in sim_results:
        for case in iteration:
            if len(case) > 0:
                sim_case_durations.append(case[-1]["time"])

    if not sim_case_durations:
        return " Simulation produced no results."

    simulated_mean = sum(sim_case_durations) / len(sim_case_durations)

    if "CASE_ID" in df_sim.columns:
        baseline_mean = df_sim.groupby("CASE_ID")["EVENT_DURATION"].sum().mean()
        baseline_case_totals = df_sim.groupby("CASE_ID")["EVENT_DURATION"].sum()
    else:
        baseline_mean = df_sim["EVENT_DURATION"].mean()
        baseline_case_totals = df_sim["EVENT_DURATION"]

    improvement = (baseline_mean - simulated_mean) / baseline_mean * 100
    color = "#2E7D32" if improvement >= 0 else "#C62828"
    direction = "faster" if improvement >= 0 else "slower"

    hist_fig = go.Figure()
    hist_fig.add_trace(go.Histogram(
        x=baseline_case_totals,
        name="Baseline Durations",
        opacity=0.6
    ))
    hist_fig.add_trace(go.Histogram(
        x=sim_case_durations,
        name="Simulated Durations",
        opacity=0.6
    ))
    hist_fig.update_layout(
        barmode="overlay",
        title="Case Duration Distribution: Baseline vs Simulation",
        xaxis_title="Total Case Duration (min)",
        yaxis_title="Count"
    )

    return html.Div([
        html.H4("Simulation Summary"),
        html.P(f"Baseline mean case duration: {baseline_mean:.2f} minutes"),
        html.P(f"Simulated mean case duration: {simulated_mean:.2f} minutes"),
        html.P(
            f"Change: {abs(improvement):.1f}% {direction}",
            style={"color": color, "fontWeight": "bold"}
        ),
        html.P(
            f"Simulation executed using Markov-chain routing and Monte-Carlo sampling "
            f"(3 iterations × 200 cases = {len(sim_case_durations)} total cases).",
            style={"color": "gray", "marginTop": "10px"}
        ),
        dcc.Graph(figure=hist_fig),
        html.P(
            "Histogram shows how case duration distribution shifts with your interventions.",
            style={"color": "gray", "fontSize": "13px"}
        )
    ])


# ============================================================
# Sync simulation with GLOBAL store (PATCHED)
# ============================================================
@callback(
    Output("simulation-log-selector", "value", allow_duplicate=True),
    Output("simulation-log-store", "data", allow_duplicate=True),
    Input("global-log-store", "data"),
    Input("simulation-log-selector", "options"),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def sync_simulation_with_global(global_store, options, pathname):

    if pathname != "/simulation":
        return no_update, no_update

    if not isinstance(global_store, dict):
        return no_update, no_update

    log_id = global_store.get("log_id")
    filename = global_store.get("filename")

    if not log_id or not options:
        return no_update, no_update

    option_values = [opt["value"] for opt in options]

    if log_id not in option_values:
        return no_update, no_update

    return log_id, {"log_id": log_id, "filename": filename}
