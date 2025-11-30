import pandas as pd
import numpy as np


# ==========================================================
# INTERNAL HELPERS
# ==========================================================

def _ensure_datetime(df):
    if "START TIME" in df:
        df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")
    if "END TIME" in df:
        df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")
    return df


def _compute_case_metrics(df):
    """
    Computes per-case metrics: duration (mins), event count.
    Returns a DataFrame indexed by CASE ID.
    """
    df = _ensure_datetime(df)

    grouped = df.groupby("CASE ID")

    durations = (grouped["END TIME"].max() - grouped["START TIME"].min()).dt.total_seconds() / 60
    event_counts = grouped.size()

    metrics = pd.DataFrame({
        "CASE_DURATION": durations,
        "EVENT_COUNT": event_counts
    })

    return metrics.reset_index()


# ==========================================================
# PUBLIC API
# ==========================================================

def list_cases(df):
    """
    Returns simple list of case IDs.
    """
    return sorted(df["CASE ID"].unique().tolist())


def get_case_metrics(df):
    """
    Returns a table of (CASE ID, duration, event count).
    """
    return _compute_case_metrics(df)


def filter_cases(
    df,
    min_duration=None,
    max_duration=None,
    min_events=None,
    max_events=None,
    system=None,
    user=None,
    start_date=None,
    end_date=None
):
    """
    Filters cases using multiple criteria.
    Returns list of CASE IDs that match all filters.
    """

    df = _ensure_datetime(df)
    metrics = _compute_case_metrics(df)

    # 1. Duration filter
    if min_duration is not None:
        metrics = metrics[metrics["CASE_DURATION"] >= min_duration]

    if max_duration is not None:
        metrics = metrics[metrics["CASE_DURATION"] <= max_duration]

    # 2. Event count filter
    if min_events is not None:
        metrics = metrics[metrics["EVENT_COUNT"] >= min_events]

    if max_events is not None:
        metrics = metrics[metrics["EVENT_COUNT"] <= max_events]

    # 3. System filter
    if system:
        sys_cases = df[df["SYSTEM NAME"] == system]["CASE ID"].unique()
        metrics = metrics[metrics["CASE ID"].isin(sys_cases)]

    # 4. User/team filter
    if user:
        user_cases = df[df["USER"] == user]["CASE ID"].unique()
        metrics = metrics[metrics["CASE ID"].isin(user_cases)]

    # 5. Start/end date filter
    if start_date:
        start_date = pd.to_datetime(start_date)
        valid_cases = df[df["START TIME"] >= start_date]["CASE ID"].unique()
        metrics = metrics[metrics["CASE ID"].isin(valid_cases)]

    if end_date:
        end_date = pd.to_datetime(end_date)
        valid_cases = df[df["END TIME"] <= end_date]["CASE ID"].unique()
        metrics = metrics[metrics["CASE ID"].isin(valid_cases)]

    return sorted(metrics["CASE ID"].tolist())


def get_case_trace(df, case_id):
    """
    Returns the full event trace for a given CASE ID,
    sorted chronologically with derived durations.
    """

    df = _ensure_datetime(df)
    case_df = df[df["CASE ID"] == case_id].sort_values("START TIME").copy()

    if "END TIME" in case_df:
        case_df["EVENT_DURATION"] = (case_df["END TIME"] - case_df["START TIME"]).dt.total_seconds() / 60

    return case_df.reset_index(drop=True)


def get_case_summary(df, case_id):
    """
    Returns a compact summary of:
      - total duration
      - number of events
      - unique activities
      - involved systems
      - involved users
    """

    trace = get_case_trace(df, case_id)

    duration = (trace["END TIME"].max() - trace["START TIME"].min()).total_seconds() / 60
    event_count = len(trace)
    unique_activities = trace["EVENT"].nunique()
    systems = sorted(trace["SYSTEM NAME"].unique())
    users = sorted(trace["USER"].unique())

    return {
        "case_id": case_id,
        "duration": duration,
        "event_count": event_count,
        "unique_activities": unique_activities,
        "systems": systems,
        "users": users,
    }
