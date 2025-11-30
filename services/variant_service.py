import pandas as pd

# ==========================================================
# Build ABSTRACT column safely
# ==========================================================
def apply_abstraction(df: pd.DataFrame, activity_type: str) -> pd.DataFrame:
    df = df.copy()
    if activity_type in df.columns:
        df["ABSTRACT"] = df[activity_type]
    else:
        df["ABSTRACT"] = df["EVENT"]
    return df


# ==========================================================
# Extract traces (variant sequences)
# ==========================================================
def extract_traces(df: pd.DataFrame) -> pd.Series:
    return df.groupby("CASE ID")["ABSTRACT"].apply(list)


# ==========================================================
# Return top K MOST FREQUENT traces
# ==========================================================
def get_top_k_traces(df: pd.DataFrame, k: int) -> list:
    traces = extract_traces(df)
    trace_counts = traces.value_counts()
    return trace_counts.head(k).index.tolist()


# ==========================================================
# Return CASE IDs belonging to the top K variants
# ==========================================================
def get_cases_for_traces(df: pd.DataFrame, trace_list: list) -> list:
    case_ids = []
    for cid, grp in df.groupby("CASE ID"):
        if grp["ABSTRACT"].tolist() in trace_list:
            case_ids.append(cid)
    return case_ids


# ==========================================================
# Main function – returns list of CASE IDs to keep
# ==========================================================
def get_top_k_variants(df: pd.DataFrame, activity_type: str, k: int):
    df = apply_abstraction(df, activity_type)
    top_traces = get_top_k_traces(df, k)
    return get_cases_for_traces(df, top_traces)
