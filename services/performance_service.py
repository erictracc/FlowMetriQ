# ================================================================
# performance_service.py
# Performance & duration analytics for event logs
# ================================================================

import pandas as pd
import numpy as np


# ----------------------------------------------------------------
# Ensure timestamps are parsed correctly
# ----------------------------------------------------------------
def _ensure_datetime(df):
    """Converts START TIME and END TIME to datetime if not already."""
    if not pd.api.types.is_datetime64_any_dtype(df["START TIME"]):
        df["START TIME"] = pd.to_datetime(df["START TIME"])

    if not pd.api.types.is_datetime64_any_dtype(df["END TIME"]):
        df["END TIME"] = pd.to_datetime(df["END TIME"])

    return df


# ================================================================
# 1. EVENT-LEVEL PERFORMANCE
# ================================================================
def get_event_durations(df):
    """
    Returns the event log with a new 'DURATION' column in seconds.
    """
    df = df.copy()
    df = _ensure_datetime(df)

    df["DURATION"] = (df["END TIME"] - df["START TIME"]).dt.total_seconds()
    return df


def get_activity_performance(df, activity_type="EVENT"):
    """
    Computes performance metrics for each activity:
    - count
    - avg duration
    - median duration
    - min/max duration
    - total duration
    """
    df = get_event_durations(df)
    df["ACT"] = df[activity_type]

    g = df.groupby("ACT")["DURATION"]

    summary = pd.DataFrame({
        "count": g.count(),
        "avg_duration": g.mean(),
        "median_duration": g.median(),
        "min_duration": g.min(),
        "max_duration": g.max(),
        "total_duration": g.sum(),
    }).reset_index()

    summary = summary.sort_values(by="avg_duration", ascending=False)

    return summary


# ================================================================
# 2. DFG PERFORMANCE (A → B average time)
# ================================================================
def compute_performance_dfg(df, activity_type="EVENT"):
    """
    Computes performance for each directly-follows relation:
        A → B:
        - frequency
        - average time between end(A) → start(B)
        - median time
        - min/max time

    Returns: dict with keys:
        (A, B) → {freq, avg_time, median_time, min_time, max_time}
    """

    df = df.copy()
    df = _ensure_datetime(df)

    df = df.sort_values(by=["CASE ID", "START TIME"])
    df["ACT"] = df[activity_type]

    # For each case, compute pair durations
    result = {}

    for _, group in df.groupby("CASE ID"):
        events = list(group["ACT"])
        end_times = list(group["END TIME"])
        start_times = list(group["START TIME"])

        for i in range(len(events) - 1):
            a, b = events[i], events[i + 1]
            duration = (start_times[i + 1] - end_times[i]).total_seconds()

            key = (a, b)
            if key not in result:
                result[key] = {"freq": 0, "times": []}

            result[key]["freq"] += 1
            result[key]["times"].append(duration)

    # Build final aggregated results
    performance_dfg = {}
    for (a, b), data in result.items():
        times = data["times"]
        performance_dfg[(a, b)] = {
            "freq": data["freq"],
            "avg_time": np.mean(times),
            "median_time": np.median(times),
            "min_time": np.min(times),
            "max_time": np.max(times)
        }

    return performance_dfg


# ================================================================
# 3. BOTTLENECK RANKING
# ================================================================
def rank_bottlenecks(perf_dfg, weight_duration=0.6, weight_frequency=0.4):
    """
    Creates a bottleneck score: frequency × average duration (weighted).
    Returns a sorted list of transitions with the highest bottleneck score.
    """

    bottlenecks = []

    for (a, b), metrics in perf_dfg.items():
        score = (
            weight_duration * metrics["avg_time"] +
            weight_frequency * metrics["freq"]
        )

        bottlenecks.append({
            "from": a,
            "to": b,
            "freq": metrics["freq"],
            "avg_time": metrics["avg_time"],
            "score": score
        })

    return sorted(bottlenecks, key=lambda x: x["score"], reverse=True)


# ================================================================
# 4. CASE-LEVEL PERFORMANCE
# ================================================================
def compute_case_durations(df):
    """
    Returns a DataFrame of:
    CASE ID | total_duration_seconds | num_events
    """

    df = _ensure_datetime(df)

    case_stats = df.groupby("CASE ID").agg(
        start=("START TIME", "min"),
        end=("END TIME", "max"),
        num_events=("EVENT", "count")
    ).reset_index()

    case_stats["total_duration"] = (
        case_stats["end"] - case_stats["start"]
    ).dt.total_seconds()

    return case_stats


def get_case_time_profile(df, case_id):
    """
    Returns a timeline of events for a specific case:
    EVENT | START | END | DURATION
    """
    df = df.copy()
    df = _ensure_datetime(df)

    case_df = df[df["CASE ID"] == case_id].sort_values("START TIME")
    case_df["DURATION"] = (
        case_df["END TIME"] - case_df["START TIME"]
    ).dt.total_seconds()

    return case_df[["EVENT", "START TIME", "END TIME", "DURATION"]]


# ================================================================
# 5. WAITING TIMES (Gaps within a case)
# ================================================================
def compute_case_waiting_times(df):
    """
    Computes the waiting time between consecutive events for each case.

    Returns a DataFrame:
    CASE ID | from | to | wait_seconds
    """

    df = df.copy()
    df = _ensure_datetime(df)

    rows = []

    for cid, group in df.groupby("CASE ID"):
        grp = group.sort_values("START TIME")

        events = list(grp["EVENT"])
        start_times = list(grp["START TIME"])
        end_times = list(grp["END TIME"])

        for i in range(len(events) - 1):
            wait = (start_times[i + 1] - end_times[i]).total_seconds()
            rows.append({
                "CASE ID": cid,
                "from": events[i],
                "to": events[i + 1],
                "wait": wait
            })

    return pd.DataFrame(rows)
