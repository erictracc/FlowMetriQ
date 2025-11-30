import pandas as pd
import numpy as np


# ==========================================================
# FAST VECTORIZED PREPROCESSING
# ==========================================================
def preprocess(df):
    df = df.copy()
    df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")
    df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")
    df["EVENT_DURATION"] = (df["END TIME"] - df["START TIME"]).dt.total_seconds() / 60
    return df


# ==========================================================
# ACTIVITY BOTTLENECKS (FAST)
# ==========================================================
def compute_activity_bottlenecks(df):
    df = preprocess(df)

    freq = df["EVENT"].value_counts()
    duration = df.groupby("EVENT")["EVENT_DURATION"].mean()

    out = pd.DataFrame({
        "EVENT": freq.index,
        "FREQUENCY": freq.values,
        "AVG_DURATION": duration.values
    })

    out["BOTTLENECK_SCORE"] = out["FREQUENCY"] * out["AVG_DURATION"]

    return out.sort_values("BOTTLENECK_SCORE", ascending=False)


# ==========================================================
# PATH BOTTLENECKS (ULTRA-FAST VECTORIZED)
# ==========================================================
def compute_path_bottlenecks(df):
    df = preprocess(df)

    # Sort by case + start time once → all transitions correct
    df = df.sort_values(["CASE ID", "START TIME"])

    # SHIFT events and times within each case
    df["NEXT_EVENT"] = df.groupby("CASE ID")["EVENT"].shift(-1)
    df["NEXT_START"] = df.groupby("CASE ID")["START TIME"].shift(-1)

    # Compute transition durations
    df["TRANSITION_DURATION"] = (
        df["NEXT_START"] - df["START TIME"]
    ).dt.total_seconds() / 60

    # Remove rows without a next event
    trans = df.dropna(subset=["NEXT_EVENT"])[["EVENT", "NEXT_EVENT", "TRANSITION_DURATION"]]

    # Frequency of transitions
    freq = (
        trans.groupby(["EVENT", "NEXT_EVENT"])
        .size()
        .reset_index(name="FREQUENCY")
    )

    # Avg duration per transition
    avg = (
        trans.groupby(["EVENT", "NEXT_EVENT"])["TRANSITION_DURATION"]
        .mean()
        .reset_index(name="AVG_DURATION")
    )

    # Merge
    out = freq.merge(avg, on=["EVENT", "NEXT_EVENT"])
    out["BOTTLENECK_SCORE"] = out["FREQUENCY"] * out["AVG_DURATION"]

    return out.sort_values("BOTTLENECK_SCORE", ascending=False)


# ==========================================================
# FULL BOTTLENECK WRAPPER (for analysis.py)
# ==========================================================
def compute_bottlenecks(df):
    return {
        "activity": compute_activity_bottlenecks(df),
        "path": compute_path_bottlenecks(df),
    }
