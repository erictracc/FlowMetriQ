import pandas as pd

# ==========================================================
# Compute directly-follows graph (DFG)
# ==========================================================
def compute_dfg(df, activity_col):
    """
    Computes directly-follows graph:
    Returns a dictionary { (A, B): count }
    """
    dfg = {}
    df_sorted = df.sort_values(by=["CASE ID", "START TIME"])

    for case, group in df_sorted.groupby("CASE ID"):
        events = list(group[activity_col])
        for i in range(len(events) - 1):
            pair = (events[i], events[i + 1])
            dfg[pair] = dfg.get(pair, 0) + 1

    return dfg


# ==========================================================
# Apply minimum frequency filter
# ==========================================================
def filter_by_frequency(dfg, min_freq):
    return {k: v for k, v in dfg.items() if v >= min_freq}


# ==========================================================
# Filter paths when user selects them
# ==========================================================
def filter_by_paths(dfg, selected_paths):
    """
    selected_paths: list like ["A|B", "B|C"]
    """
    if not selected_paths:
        return dfg

    allowed = {tuple(p.split("|")) for p in selected_paths}
    return {k: v for k, v in dfg.items() if k in allowed}


# ==========================================================
# Build Cytoscape graph elements
# ==========================================================
def build_cytoscape_elements(dfg):
    """
    Converts DFG dict into Cytoscape node + edge elements
    """
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


# ==========================================================
# Main helper used in callbacks
# ==========================================================
def compute_dfg_graph(df, activity_type, min_freq, top_variant_cases, filter_paths):
    """
    Full pipeline to compute the DFG graph elements.
    - df                     → pandas DataFrame
    - activity_type          → "EVENT", "ACTIVITY", etc.
    - min_freq               → slider value
    - top_variant_cases      → subset of CASE IDs (optional)
    - filter_paths           → dropdown-selected paths (optional)
    """
    df = df.copy()

    # Activity abstraction
    if activity_type not in df.columns:
        activity_type = "EVENT"

    df["ABSTRACT"] = df[activity_type]

    # Restrict by variants (if given)
    if top_variant_cases is not None:
        df = df[df["CASE ID"].isin(top_variant_cases)]

    # Compute base DFG
    dfg = compute_dfg(df, "ABSTRACT")

    # Min frequency
    dfg = filter_by_frequency(dfg, min_freq)

    # Filter selected paths
    dfg = filter_by_paths(dfg, filter_paths)

    # Build graph elements
    return build_cytoscape_elements(dfg)
