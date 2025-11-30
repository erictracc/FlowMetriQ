import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import pandas as pd
import base64
import io
import dash_cytoscape as cyto
from flask import current_app as server
from bson import ObjectId

# Import DFG helpers from service layer
from services.dfg_service import compute_dfg, compute_dfg_graph

cyto.load_extra_layouts()

dash.register_page(__name__, path="/home", title="Dashboard")


# ==========================================================
# Helper: Load DF from memory → or fallback from MongoDB
# ==========================================================
def load_df(log_id):
    # Check server cache first
    if hasattr(server, "LOG_STORE") and log_id in server.LOG_STORE:
        return server.LOG_STORE[log_id]

    # If not cached: load from MongoDB
    db = server.db
    doc = db.event_logs.find_one({"_id": ObjectId(log_id)})
    if doc:
        df = pd.DataFrame(doc["events"])

        # Re-cache for fast DFG interactions
        if not hasattr(server, "LOG_STORE"):
            server.LOG_STORE = {}
        server.LOG_STORE[log_id] = df

        return df

    return None


# ==========================================================
# PAGE LAYOUT
# ==========================================================
layout = html.Div(
    style={"display": "flex", "fontFamily": "Arial", "height": "100vh"},
    children=[

        # ==========================
        # LEFT SIDEBAR
        # ==========================
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

                # Upload section
                html.Label("Upload Event Log"),
                dcc.Upload(
                    id="upload-log-home",
                    children=html.Div("Drag & Drop or Click", style={"textAlign": "center"}),
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
                    value=10,
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
                    value=3,
                    style={"marginBottom": "30px"},
                ),

                html.Label("Zoom"),
                dcc.Slider(
                    id="dfg-zoom",
                    min=0,
                    max=3,
                    step=0.5,
                    value=1,
                    tooltip={"placement": "bottom"},
                    marks={},   # no labels
                ),

                html.Div(style={"marginBottom": "30px"}),

                html.Hr(),

                # =============================
                # DELETE BUTTON
                # =============================
                html.Button(
                    "Delete Selected Log",
                    id="delete-log-btn",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "backgroundColor": "#C62828",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "cursor": "pointer",
                        "marginTop": "20px",
                    },
                    disabled=True,
                ),

                html.Div(id="delete-status", style={"marginTop": "10px", "color": "#C62828"}),
            ],
        ),

        # ==========================
        # MAIN CONTENT
        # ==========================
        html.Div(
            style={"flex": 1, "padding": "20px"},
            children=[

                # TOP BAR
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

                        # Select previously uploaded logs from Mongo
                        dcc.Dropdown(
                            id="log-selector",
                            options=[],
                            placeholder="Select loaded log",
                            style={"width": "250px"},
                        ),
                    ],
                ),

                # Graph
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


# ==========================================================
# Upload Log → Save to Mongo + Cache locally
# ==========================================================
@callback(
    Output("home-upload-status", "children"),
    Output("global-log-store", "data"),
    Output("global-log-name", "data"),
    Input("upload-log-home", "contents"),
    State("upload-log-home", "filename"),
)
def handle_upload(contents, filename):
    if contents is None:
        return "", None, None

    try:
        data = base64.b64decode(contents.split(",")[1]).decode("utf-8")
        df = pd.read_csv(io.StringIO(data))

        # Save to MongoDB
        db = server.db
        log_doc = {
            "filename": filename,
            "columns": list(df.columns),
            "n_events": len(df),
            "n_cases": df["CASE ID"].nunique() if "CASE ID" in df else None,
            "events": df.to_dict("records"),
        }
        inserted = db.event_logs.insert_one(log_doc)
        log_id = str(inserted.inserted_id)

        # Cache in memory
        if not hasattr(server, "LOG_STORE"):
            server.LOG_STORE = {}
        server.LOG_STORE[log_id] = df

        return f"Uploaded file: {filename}", log_id, filename

    except Exception as e:
        return f"Upload failed: {str(e)}", None, None


# ==========================================================
# Populate dropdown with ALL Mongo logs on page load
# ==========================================================
@callback(
    Output("log-selector", "options"),
    Input("url", "pathname"),
)
def populate_log_dropdown(_):
    db = server.db
    logs = list(db.event_logs.find({}, {"filename": 1}))
    return [{"label": log["filename"], "value": str(log["_id"])} for log in logs]


# ==========================================================
# Selecting a log reloads it from Mongo into global stores
# + enables delete button
# ==========================================================
@callback(
    Output("global-log-store", "data", allow_duplicate=True),
    Output("global-log-name", "data", allow_duplicate=True),
    Output("delete-log-btn", "disabled", allow_duplicate=True),
    Input("log-selector", "value"),
    prevent_initial_call=True,
)
def load_selected_log(log_id):
    if not log_id:
        return None, None, True

    df = load_df(log_id)
    if df is None:
        return None, None, True

    doc = server.db.event_logs.find_one({"_id": ObjectId(log_id)})
    filename = doc["filename"]

    # enable delete button
    return log_id, filename, False


# ==========================================================
# Populate Filter Paths
# ==========================================================
@callback(
    Output("filter-paths", "options"),
    Input("global-log-store", "data"),
)
def populate_filter_paths(log_id):
    if not log_id:
        return []

    df = load_df(log_id)
    if df is None or "EVENT" not in df.columns:
        return []

    # Use the service-layer DFG helper directly on EVENT
    dfg = compute_dfg(df, "EVENT")

    return [{"label": f"{a} → {b}", "value": f"{a}|{b}"} for (a, b) in dfg.keys()]


# ==========================================================
# Generate DFG Graph
# ==========================================================
@callback(
    Output("dfg-graph", "elements"),
    Input("global-log-store", "data"),
    Input("event-abstraction", "value"),
    Input("min-frequency", "value"),
    Input("top-variants", "value"),
    Input("filter-paths", "value"),
    Input("refresh-graph", "n_clicks"),
)
def update_dfg(log_id, activity_type, min_freq, top_variants, filter_paths, refresh):
    if not log_id:
        return []

    df = load_df(log_id)
    if df is None:
        return []

    df = df.copy()

    # ---------- Top Variants (same behavior as before) ----------
    top_variant_cases = None
    if top_variants != "none":
        k = int(top_variants)

        # Use the current abstraction when defining traces
        if activity_type in df.columns:
            df["ABSTRACT"] = df[activity_type]
        else:
            df["ABSTRACT"] = df["EVENT"]

        traces = (
            df.groupby("CASE ID")["ABSTRACT"]
            .apply(list)
            .value_counts()
        )
        top_traces = traces.head(k).index.tolist()

        top_variant_cases = [
            cid for cid, grp in df.groupby("CASE ID")
            if grp["ABSTRACT"].tolist() in top_traces
        ]

    # ---------- Delegate DFG + filtering to service ----------
    return compute_dfg_graph(
        df=df,
        activity_type=activity_type,
        min_freq=min_freq,
        top_variant_cases=top_variant_cases,
        filter_paths=filter_paths,
    )


# ==========================================================
# Zoom Handling
# ==========================================================
@callback(
    Output("dfg-graph", "zoom"),
    Input("dfg-zoom", "value")
)
def update_zoom(val):
    # direct mapping slider → cytoscape zoom
    return val


# ==========================================================
# DELETE LOG
# ==========================================================
@callback(
    Output("delete-status", "children"),
    Output("log-selector", "value", allow_duplicate=True),
    Output("log-selector", "options", allow_duplicate=True),
    Output("global-log-store", "data", allow_duplicate=True),
    Output("global-log-name", "data", allow_duplicate=True),
    Output("delete-log-btn", "disabled", allow_duplicate=True),
    Input("delete-log-btn", "n_clicks"),
    State("log-selector", "value"),
    prevent_initial_call=True,
)
def delete_log(n, log_id):
    if not log_id:
        return "", None, no_update, None, None, True

    db = server.db
    db.event_logs.delete_one({"_id": ObjectId(log_id)})

    if hasattr(server, "LOG_STORE"):
        server.LOG_STORE.pop(log_id, None)

    logs = list(db.event_logs.find({}, {"filename": 1}))
    opts = [{"label": l["filename"], "value": str(l["_id"])} for l in logs]

    return (
        "Log deleted.",
        None,
        opts,
        None,
        None,
        True,
    )
