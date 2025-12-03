import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# SERVICES
from services.log_service import load_df, list_logs
from services.bottleneck_service import compute_bottlenecks
from services.graph_service import (
    event_frequency_bar,
    duration_distribution,
    duration_boxplot,
    event_timeseries,
)

dash.register_page(__name__, path="/analysis", title="Process Analysis")


# ============================================
# Helpers
# ============================================
def stat_card(title, value, color="#1976D2"):
    return html.Div(
        style={
            "padding": "18px",
            "backgroundColor": color,
            "color": "white",
            "borderRadius": "8px",
            "flex": "1",
            "minWidth": "200px",
            "marginRight": "15px",
            "textAlign": "center",
        },
        children=[
            html.Div(title, style={"fontSize": "14px", "opacity": 0.9}),
            html.Div(value, style={"fontSize": "24px", "fontWeight": "bold"}),
        ],
    )


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Clean df, ensure datetime, ensure CASE ID is normalized."""
    df = df.copy()

    if "CASE ID" in df.columns:
        df["CASE ID"] = df["CASE ID"].astype(str).str.strip()

    # Convert timestamps
    if "START TIME" in df.columns:
        df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")

    if "END TIME" in df.columns:
        df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")

    # Compute event duration
    if "END TIME" in df.columns and "START TIME" in df.columns:
        df["EVENT_DURATION"] = (
            df["END TIME"] - df["START TIME"]
        ).dt.total_seconds() / 60.0
    else:
        df["EVENT_DURATION"] = pd.NA

    return df


def compute_activity_performance(df: pd.DataFrame) -> pd.DataFrame:
    if "EVENT" not in df.columns:
        return pd.DataFrame(
            columns=["EVENT", "FREQUENCY", "AVG_DURATION", "TOTAL_DURATION"]
        )

    grouped = (
        df.groupby("EVENT")
        .agg(
            FREQUENCY=("EVENT", "count"),
            AVG_DURATION=("EVENT_DURATION", "mean"),
            TOTAL_DURATION=("EVENT_DURATION", "sum"),
        )
        .reset_index()
    )

    return grouped.sort_values("FREQUENCY", ascending=False)


def compute_case_stats(df: pd.DataFrame) -> pd.DataFrame:
    if "CASE ID" not in df.columns:
        return pd.DataFrame(
            columns=["CASE ID", "total_duration", "start", "end", "n_events"]
        )

    grouped = (
        df.groupby("CASE ID")
        .agg(
            total_duration=("EVENT_DURATION", "sum"),
            start=("START TIME", "min"),
            end=("END TIME", "max"),
            n_events=("EVENT", "count"),
        )
        .reset_index()
    )

    return grouped


# ============================================
# Page Layout
# ============================================
layout = html.Div(
    style={"padding": "20px", "fontFamily": "Arial"},
    children=[
        # TOP FILTER BAR
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "flexWrap": "wrap",
                "marginBottom": "25px",
                "alignItems": "center",
            },
            children=[
                html.Div(
                    style={"minWidth": "220px", "flex": "1"},
                    children=[
                        html.Label("Select Log"),
                        dcc.Dropdown(
                            id="analysis-log-selector",
                            options=[],
                            placeholder="Select loaded log",
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "220px",                    "flex": "1"},
                    children=[
                        html.Label("Case Viewer"),
                        dcc.Dropdown(
                            id="case-selector",
                            placeholder="Select a Case ID",
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "200px", "flex": "1"},
                    children=[
                        html.Label("Event Type Filter"),
                        dcc.Dropdown(
                            id="event-filter",
                            multi=True,
                            placeholder="Filter events...",
                            value=[],
                        ),
                    ],
                ),

                # -------------- TEAM FILTER ADDED HERE --------------
                html.Div(
                    style={"minWidth": "200px", "flex": "1"},
                    children=[
                        html.Label("Team Filter"),
                        dcc.Dropdown(
                            id="team-filter",
                            multi=True,
                            placeholder="Filter by team...",
                            value=[],
                        ),
                    ],
                ),

                html.Div(
                    style={"minWidth": "260px"},
                    children=[
                        html.Label("Date Range"),
                        dcc.DatePickerRange(
                            id="date-range-filter",
                            min_date_allowed=None,
                            max_date_allowed=None,
                        ),
                    ],
                ),

                # RUN ANALYSIS
                html.Button(
                    "Run Analysis",
                    id="run-analysis",
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

        html.H2("Process Performance Dashboard", style={"marginBottom": "20px"}),

        # STAT CARDS
        html.Div(
            id="analysis-stat-cards",
            style={"display": "flex", "flexWrap": "wrap", "marginBottom": "25px"},
        ),

        html.H3("Activity Performance"),
        dash_table.DataTable(
            id="performance-table",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center"},
        ),

        html.Hr(style={"margin": "30px 0"}),

        html.H3("Top Bottlenecks"),
        dash_table.DataTable(
            id="bottleneck-table",
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center"},
        ),

        html.Hr(style={"margin": "30px 0"}),

        html.H3("Case Timeline"),
        dcc.Graph(id="case-timeline"),

        html.Hr(style={"margin": "40px 0"}),
        html.H3("Additional Visual Insights"),

        dcc.Graph(id="graph-event-frequency"),
        dcc.Graph(id="graph-duration-dist"),
        dcc.Graph(id="graph-duration-box"),
        dcc.Graph(id="graph-timeseries"),
    ],
)


# ============================================
# Populate Log List
# ============================================
@callback(
    Output("analysis-log-selector", "options"),
    Output("analysis-log-selector", "value", allow_duplicate=True),
    Input("global-log-store", "data"),
    Input("url", "pathname"),
    prevent_initial_call="initial_duplicate",
)
def populate_logs(global_log, pathname):

    logs = list_logs()
    options = [{"label": l["filename"], "value": str(l["_id"])} for l in logs]

    # Auto-select only when entering Analysis page
    if pathname == "/analysis":
        if isinstance(global_log, dict):
            log_id = global_log.get("log_id")
            if log_id and log_id in [o["value"] for o in options]:
                return options, log_id

    return options, dash.no_update


# ============================================
# INITIAL LOAD → Populate filters + initial metrics
# ============================================
@callback(
    Output("case-selector", "options"),
    Output("event-filter", "options"),
    Output("event-filter", "value"),
    Output("team-filter", "options"),
    Output("team-filter", "value"),
    Output("date-range-filter", "min_date_allowed"),
    Output("date-range-filter", "max_date_allowed"),
    Output("date-range-filter", "start_date"),
    Output("date-range-filter", "end_date"),
    Output("analysis-stat-cards", "children"),
    Output("performance-table", "data"),
    Output("performance-table", "columns"),
    Output("bottleneck-table", "data"),
    Output("bottleneck-table", "columns"),
    Input("analysis-log-selector", "value"),
)
def load_log_and_initial_analysis(log_id):

    if not log_id:
        return [], [], [], [], [], None, None, None, None, [], [], [], [], []

    df = load_df(log_id)
    if df is None or df.empty:
        return [], [], [], [], [], None, None, None, None, [], [], [], [], []

    df = preprocess(df)

    # CASE LIST
    case_stats = compute_case_stats(df)
    case_options = [{"label": str(c), "value": str(c)} for c in case_stats["CASE ID"]]

    # EVENT FILTER OPTIONS
    event_types = sorted(df["EVENT"].dropna().unique())
    event_options = [{"label": e, "value": e} for e in event_types]

    # TEAM FILTER OPTIONS
    if "TEAM" in df.columns:
        team_types = sorted(df["TEAM"].dropna().unique())
        team_options = [{"label": t, "value": t} for t in team_types]
    else:
        team_options = []

    # DATE RANGE
    min_date = df["START TIME"].min()
    max_date = df["START TIME"].max()

    # STAT CARDS
    total_cases = len(case_stats)
    total_events = len(df)
    avg_case_time = case_stats["total_duration"].mean()

    cards = [
        stat_card("Total Cases", total_cases),
        stat_card("Total Events", total_events),
        stat_card("Avg Case Duration (min)", f"{avg_case_time:.1f}"),
    ]

    # PERFORMANCE TABLE
    perf_df = compute_activity_performance(df)
    perf_data = perf_df.to_dict("records")
    perf_columns = [{"name": c, "id": c} for c in perf_df.columns]

    # BOTTLENECK TABLE
    bottlenecks = compute_bottlenecks(df)
    bottleneck_df = bottlenecks["path"]
    bottleneck_data = bottleneck_df.to_dict("records")
    bottleneck_columns = [{"name": c, "id": c} for c in bottleneck_df.columns]

    return (
        case_options,
        event_options,
        [],
        team_options,
        [],
        min_date,
        max_date,
        min_date,
        max_date,
        cards,
        perf_data,
        perf_columns,
        bottleneck_data,
        bottleneck_columns,
    )


# ============================================
# RUN ANALYSIS — filtered computation
# ============================================
@callback(
    Output("analysis-stat-cards", "children", allow_duplicate=True),
    Output("performance-table", "data", allow_duplicate=True),
    Output("performance-table", "columns", allow_duplicate=True),
    Output("bottleneck-table", "data", allow_duplicate=True),
    Output("bottleneck-table", "columns", allow_duplicate=True),
    Input("run-analysis", "n_clicks"),
    State("analysis-log-selector", "value"),
    State("case-selector", "value"),
    State("event-filter", "value"),
    State("team-filter", "value"),
    State("date-range-filter", "start_date"),
    State("date-range-filter", "end_date"),
    prevent_initial_call=True,
)
def run_analysis(_, log_id, case_id, event_filter, team_filter, start_date, end_date):

    if not log_id:
        return [], [], [], [], []

    df = load_df(log_id)
    if df is None or df.empty:
        return [], [], [], [], []

    df = preprocess(df)

    # APPLY FILTERS
    filtered = df.copy()

    if event_filter:
        filtered = filtered[filtered["EVENT"].isin(event_filter)]

    if team_filter:
        filtered = filtered[filtered["TEAM"].isin(team_filter)]

    if case_id:
        filtered = filtered[filtered["CASE ID"] == str(case_id)]

    if start_date and end_date:
        start_ts, end_ts = pd.to_datetime(start_date), pd.to_datetime(end_date)
        filtered = filtered[
            (filtered["START TIME"] >= start_ts)
            & (filtered["START TIME"] <= end_ts)
        ]

    if filtered.empty:
        return [], [], [], [], []

    # STAT CARDS
    case_stats = compute_case_stats(filtered)
    total_cases = len(case_stats)
    total_events = len(filtered)
    avg_case_time = case_stats["total_duration"].mean()

    cards = [
        stat_card("Total Cases", total_cases),
        stat_card("Total Events", total_events),
        stat_card("Avg Case Duration (min)", f"{avg_case_time:.1f}"),
    ]

    # PERFORMANCE TABLE
    perf_df = compute_activity_performance(filtered)
    perf_data = perf_df.to_dict("records")
    perf_columns = [{"name": c, "id": c} for c in perf_df.columns]

    # BOTTLENECKS
    bottlenecks = compute_bottlenecks(filtered)
    bottleneck_df = bottlenecks["path"]
    bottleneck_data = bottleneck_df.to_dict("records")
    bottleneck_columns = [{"name": c, "id": c} for c in bottleneck_df.columns]

    return cards, perf_data, perf_columns, bottleneck_data, bottleneck_columns


# ============================================
# CASE TIMELINE (same filtering logic)
# ============================================
@callback(
    Output("case-timeline", "figure"),
    Input("run-analysis", "n_clicks"),
    State("analysis-log-selector", "value"),
    State("case-selector", "value"),
    State("event-filter", "value"),
    State("team-filter", "value"),
    State("date-range-filter", "start_date"),
    State("date-range-filter", "end_date"),
)
def show_case_timeline(_, log_id, case_id, event_filter, team_filter, start_date, end_date):

    fig = go.Figure()

    if not log_id or not case_id:
        return fig

    df = load_df(log_id)
    if df is None or df.empty:
        return fig

    df = preprocess(df)

    # MATCH ANALYSIS FILTERS
    filtered = df.copy()

    if event_filter:
        filtered = filtered[filtered["EVENT"].isin(event_filter)]

    if team_filter:
        filtered = filtered[filtered["TEAM"].isin(team_filter)]

    if start_date and end_date:
        start_ts, end_ts = pd.to_datetime(start_date), pd.to_datetime(end_date)
        filtered = filtered[
            (filtered["START TIME"] >= start_ts)
            & (filtered["START TIME"] <= end_ts)
        ]

    case_df = filtered[filtered["CASE ID"] == str(case_id)]

    if case_df.empty:
        fig.update_layout(height=300, title=f"⚠️ No events found for Case {case_id}")
        return fig

    # TIMELINE
    fig = px.timeline(
        case_df.sort_values("START TIME"),
        x_start="START TIME",
        x_end="END TIME",
        y="EVENT",
        color="EVENT",
    )

    fig.update_layout(
        height=400,
        title=f"Case {case_id} Timeline",
        xaxis_title="Time",
        yaxis_title="Event",
        margin=dict(l=40, r=20, t=50, b=40),
    )

    return fig


# ============================================
# ADDITIONAL INSIGHTS (not filtered — full log)
# ============================================
@callback(
    Output("graph-event-frequency", "figure"),
    Output("graph-duration-dist", "figure"),
    Output("graph-duration-box", "figure"),
    Output("graph-timeseries", "figure"),
    Input("analysis-log-selector", "value"),
)
def update_graphs_for_log(log_id):

    if not log_id:
        empty = go.Figure()
        return empty, empty, empty, empty

    df = load_df(log_id)
    if df is None or df.empty:
        empty = go.Figure()
        return empty, empty, empty, empty

    df = preprocess(df)

    # Full log used intentionally
    return (
        event_frequency_bar(df),
        duration_distribution(df),
        duration_boxplot(df),
        event_timeseries(df),
    )
