import dash
from dash import html, dcc, callback, Input, Output, State
import pandas as pd
import base64
import io
from flask import current_app as server
import dash_cytoscape as cyto

cyto.load_extra_layouts()

dash.register_page(__name__, path="/home", title="Dashboard")

# ---------------------------------------------------------
# Helper: Compute DFG
# ---------------------------------------------------------
def compute_dfg(df, activity_col):
    dfg = {}
    df_sorted = df.sort_values(by=["CASE ID", "START TIME"])

    for case, group in df_sorted.groupby("CASE ID"):
        events = list(group[activity_col])
        for i in range(len(events) - 1):
            pair = (events[i], events[i + 1])
            dfg[pair] = dfg.get(pair, 0) + 1

    return dfg


# ---------------------------------------------------------
# PAGE LAYOUT
# ---------------------------------------------------------
layout = html.Div(
    style={"display": "flex", "fontFamily": "Arial", "height": "100vh"},
    children=[

        # LEFT SIDEBAR
        html.Div(
            style={
                "width": "270px",
                "minWidth": "240px",
                "backgroundColor": "#F4F6F9",
                "padding": "20px",
                "borderRight": "1px solid #DDD",
                "overflowY": "auto",
            },
            children=[

                html.H4("Settings", style={"marginBottom": "20px"}),

                html.Label("Filter Paths"),
                dcc.Dropdown(
                    id="filter-paths",
                    options=[],
                    placeholder="(No log loaded)",
                    multi=True,
                    style={"marginBottom": "20px"},
                ),

                html.Label("Event Types"),
                dcc.Checklist(
                    id="event-type-checklist",
                    options=[],
                    value=[],
                    style={"marginBottom": "20px"},
                ),

                html.Hr(),

                html.Label("Upload Event Log"),
                dcc.Upload(
                    id="upload-log-home",
                    children=html.Div("Drag & Drop or Click",
                                      style={"textAlign": "center"}),
                    multiple=False,
                    style={
                        "width": "100%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "2px",
                        "borderStyle": "dashed",
                        "borderRadius": "6px",
                        "textAlign": "center",
                        "backgroundColor": "white",
                        "cursor": "pointer",
                        "marginBottom": "10px",
                    },
                ),
                html.Div(id="home-upload-status"),

                html.Hr(),

                html.Label("Event Abstraction"),
                dcc.Dropdown(
                    id="event-abstraction",
                    options=[
                        {"label": "Event", "value": "EVENT"},
                        {"label": "Activity", "value": "ACTIVITY"},
                        {"label": "Task", "value": "TASK"},
                        {"label": "System", "value": "SYSTEM NAME"},
                    ],
                    value="EVENT",
                    clearable=False,
                    style={"marginBottom": "20px"},
                ),

                html.Label("Minimum Frequency"),
                dcc.Slider(
                    id="min-frequency",
                    min=1,
                    max=50,
                    step=1,
                    value=1,
                    tooltip={"placement": "bottom"},
                    marks={i: str(i) for i in [1, 10, 20, 30, 40, 50]},
                ),
                html.Div(style={"marginBottom": "30px"}),

                html.Label("Top Variants"),
                dcc.Dropdown(
                    id="top-variants",
                    options=[
                        {"label": "None (full model)", "value": "none"},
                        {"label": "Top 3 variants", "value": 3},
                        {"label": "Top 5 variants", "value": 5},
                        {"label": "Top 10 variants", "value": 10},
                    ],
                    value="none",
                    style={"marginBottom": "30px"},
                ),

                html.Label("Zoom"),
                dcc.Slider(
                    id="dfg-zoom",
                    min=0.2,
                    max=2.5,
                    step=0.1,
                    value=1.0,
                    tooltip={"placement": "bottom"},
                    marks={},   # REMOVE SCALE LABELS
                ),
            ],
        ),

        # MAIN CONTENT
        html.Div(
            style={"flex": 1, "padding": "20px"},
            children=[

                html.Div(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "space-between",
                        "marginBottom": "15px",
                    },
                    children=[

                        html.Button(
                            "Refresh Graph",
                            id="refresh-graph",
                            n_clicks=0,
                            style={
                                "padding": "8px 14px",
                                "fontSize": "16px",
                                "borderRadius": "6px",
                                "backgroundColor": "#1976D2",
                                "color": "white",
                                "border": "none",
                                "cursor": "pointer",
                            },
                        ),

                        dcc.Dropdown(
                            id="log-selector",
                            options=[],
                            placeholder="Select loaded log",
                            style={"width": "250px"},
                        ),       
                    ],
                ),

                cyto.Cytoscape(
                    id="dfg-graph",
                    responsive=True,
                    minZoom=0.2,
                    maxZoom=2.5,
                    userZoomingEnabled=True,

                    layout={
                        "name": "dagre",
                        "rankDir": "TB",
                        "animate": False,
                        "fit": False,
                        "padding": 0
                    },

                    style={
                        "width": "100%",
                        "height": "calc(100vh - 180px)",
                        "backgroundColor": "white",
                    },

                    elements=[],
                    stylesheet=[
                        {
                            "selector": "node",
                            "style": {
                                "content": "data(label)",
                                "text-valign": "center",
                                "text-halign": "center",
                                "color": "white",
                                "background-color": "#1976D2",
                                "padding": "10px",
                                "font-size": "15px",
                                "shape": "round-rectangle",
                                "width": "label",
                                "height": "label",
                                "text-wrap": "wrap",
                                "text-max-width": 150,
                            },
                        },
                        {
                            "selector": "edge",
                            "style": {
                                "curve-style": "taxi",
                                "taxi-direction": "vertical",
                                "target-arrow-shape": "triangle",
                                "line-color": "#90CAF9",
                                "target-arrow-color": "#90CAF9",
                                "label": "data(weight)",
                                "font-size": "11px",
                                "text-background-color": "white",
                                "text-background-opacity": 0.7,
                                "text-background-padding": "3px",
                            },
                        },
                    ],
                ),
            ],
        ),
    ],
)


# ---------------------------------------------------------
# Upload handler
# ---------------------------------------------------------
@callback(
    Output("home-upload-status", "children"),
    Output("global-log-name", "data"),
    Input("upload-log-home", "contents"),
    State("upload-log-home", "filename"),
)
def handle_upload(contents, filename):
    if contents is None:
        return "", None

    try:
        decoded = base64.b64decode(contents.split(",")[1]).decode("utf-8")
        df = pd.read_csv(io.StringIO(decoded))

        server.config["log_df"] = df
        server.config["log_name"] = filename

        return f"Uploaded file: {filename}", filename

    except Exception as e:
        return f"Upload failed: {str(e)}", None


# ---------------------------------------------------------
# Dropdown update
# ---------------------------------------------------------
@callback(
    Output("log-selector", "options"),
    Output("log-selector", "value"),
    Input("global-log-name", "data"),
)
def update_dropdown(filename):
    if filename is None:
        return [], None
    return [{"label": filename, "value": filename}], filename


# ---------------------------------------------------------
# Populate Filter Paths
# ---------------------------------------------------------
@callback(
    Output("filter-paths", "options"),
    Input("global-log-name", "data")
)
def populate_filter_paths(filename):
    df = server.config.get("log_df")
    if df is None:
        return []

    df["ABSTRACT"] = df["EVENT"]
    dfg = compute_dfg(df, "ABSTRACT")

    return [
        {"label": f"{a} → {b}", "value": f"{a}|{b}"}
        for (a, b) in dfg.keys()
    ]


# ---------------------------------------------------------
# Generate DFG Graph (WITH REAL TOP VARIANTS)
# ---------------------------------------------------------
@callback(
    Output("dfg-graph", "elements"),
    Input("log-selector", "value"),
    Input("event-abstraction", "value"),
    Input("min-frequency", "value"),
    Input("top-variants", "value"),
    Input("filter-paths", "value"),
    Input("refresh-graph", "n_clicks"),
)
def update_dfg(selected_log, activity_type, min_freq, top_variants, filter_paths, refresh):
    df = server.config.get("log_df")
    if df is None:
        return []

    # fallback
    if activity_type not in df.columns:
        activity_type = "EVENT"

    df["ABSTRACT"] = df[activity_type]

    # ---- Top Variant Filtering ----
    if top_variants != "none":
        k = int(top_variants)

        traces = (
            df.groupby("CASE ID")["ABSTRACT"]
            .apply(list)
            .value_counts()
        )

        top_traces = traces.head(k).index.tolist()

        allowed_caseids = [
            cid for cid, grp in df.groupby("CASE ID")
            if grp["ABSTRACT"].tolist() in top_traces
        ]

        df = df[df["CASE ID"].isin(allowed_caseids)]

    # ---- Compute DFG ----
    dfg = compute_dfg(df, "ABSTRACT")

    # minimum frequency filter
    dfg = {k: v for k, v in dfg.items() if v >= min_freq}

    # filter paths
    if filter_paths:
        allowed = {tuple(fp.split("|")) for fp in filter_paths}
        dfg = {k: v for k, v in dfg.items() if k in allowed}

    # ---- Build Graph ----
    nodes = {}
    edges = []

    for (a, b), weight in dfg.items():
        nodes[a] = True
        nodes[b] = True
        edges.append({
            "data": {"source": a, "target": b, "weight": weight}
        })

    node_elements = [{"data": {"id": n, "label": n}} for n in nodes]
    return node_elements + edges


# ---------------------------------------------------------
# Zoom Handling
# ---------------------------------------------------------
@callback(
    Output("dfg-graph", "zoom"),
    Input("dfg-zoom", "value")
)
def update_zoom(val):
    return val
