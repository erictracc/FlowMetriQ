import pandas as pd
import numpy as np

# ==========================================================
# BASIC DATA CLEANING HELPERS
# ==========================================================

def ensure_datetime(df):
    """Ensures START TIME and END TIME are converted to datetime."""
    if "START TIME" in df:
        df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")
    if "END TIME" in df:
        df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")
    return df

def compute_durations(df):
    """Adds an EVENT_DURATION column if not present."""
    if "START TIME" in df and "END TIME" in df:
        df["EVENT_DURATION"] = (df["END TIME"] - df["START TIME"]).dt.total_seconds() / 60
    else:
        df["EVENT_DURATION"] = None
    return df


# ==========================================================
# GENERAL STATISTICS
# ==========================================================

def get_global_stats(df):
    """Returns a dictionary of global dataset-level statistics."""

    df = ensure_datetime(df)
    df = compute_durations(df)

    total_cases = df["CASE ID"].nunique()
    total_events = len(df)
    total_users = df["USER"].nunique() if "USER" in df else None
    total_systems = df["SYSTEM NAME"].nunique() if "SYSTEM NAME" in df else None

    # Case durations
    case_times = (
        df.groupby("CASE ID")
        .apply(lambda g: (g["END TIME"].max() - g["START TIME"].min()).total_seconds() / 60)
    )

    avg_case_duration = round(case_times.mean(), 2)
    median_case_duration = round(case_times.median(), 2)

    return {
        "total_cases": total_cases,
        "total_events": total_events,
        "total_users": total_users,
        "total_systems": total_systems,
        "avg_case_duration": avg_case_duration,
        "median_case_duration": median_case_duration,
    }


# ==========================================================
# ACTIVITY STATS
# ==========================================================

def get_activity_frequency(df):
    """Returns activity frequency as a sorted dataframe."""
    freq = df["EVENT"].value_counts().reset_index()
    freq.columns = ["EVENT", "COUNT"]
    return freq


def get_activity_durations(df):
    """Returns mean duration per activity."""
    df = ensure_datetime(df)
    df = compute_durations(df)

    if "EVENT_DURATION" not in df:
        return pd.DataFrame(columns=["EVENT", "AVG_DURATION"])

    out = (
        df.groupby("EVENT")["EVENT_DURATION"]
        .mean()
        .reset_index()
        .rename(columns={"EVENT_DURATION": "AVG_DURATION"})
    )

    return out.sort_values("AVG_DURATION", ascending=False)


# ==========================================================
# CASE STATISTICS
# ==========================================================

def get_case_durations(df):
    """Returns min/max timestamps per case + duration."""
    df = ensure_datetime(df)
    df = compute_durations(df)

    case_times = (
        df.groupby("CASE ID")
        .apply(lambda g: (g["END TIME"].max() - g["START TIME"].min()).total_seconds() / 60)
        .reset_index()
    )
    case_times.columns = ["CASE ID", "CASE_DURATION"]

    return case_times.sort_values("CASE_DURATION", ascending=False)


def get_case_event_counts(df):
    """Returns number of events per case."""
    counts = (
        df.groupby("CASE ID")["EVENT"]
        .count()
        .reset_index()
        .rename(columns={"EVENT": "NUM_EVENTS"})
    )
    return counts.sort_values("NUM_EVENTS", ascending=False)


# ==========================================================
# SYSTEM STATISTICS
# ==========================================================

def get_system_frequency(df):
    if "SYSTEM NAME" not in df:
        return pd.DataFrame(columns=["SYSTEM NAME", "COUNT"])
    freq = df["SYSTEM NAME"].value_counts().reset_index()
    freq.columns = ["SYSTEM NAME", "COUNT"]
    return freq


def get_system_durations(df):
    df = ensure_datetime(df)
    df = compute_durations(df)
    if "SYSTEM NAME" not in df:
        return pd.DataFrame(columns=["SYSTEM NAME", "AVG_DURATION"])
    return (
        df.groupby("SYSTEM NAME")["EVENT_DURATION"]
        .mean()
        .reset_index()
        .rename(columns={"EVENT_DURATION": "AVG_DURATION"})
    )

