import pandas as pd
import numpy as np
from bson import ObjectId
from flask import current_app as server


# ==========================================================
# INTERNAL: Preprocess DF ONCE per log
# ==========================================================
def _preprocess_df(df_raw):
    """
    Heavy preprocessing — runs ONCE per uploaded log.
    Everything stored in cache for fast analysis.
    """

    df = df_raw.copy()

    # -------- 1) Datetime conversion ----------
    if "START TIME" in df:
        df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")
    if "END TIME" in df:
        df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")

    # -------- 2) Event duration (minutes) -----
    if "START TIME" in df and "END TIME" in df:
        df["EVENT_DURATION"] = (
            df["END TIME"] - df["START TIME"]
        ).dt.total_seconds() / 60
    else:
        df["EVENT_DURATION"] = np.nan

    # -------- 3) Sort for transitions ----------
    df = df.sort_values(["CASE ID", "START TIME"]).reset_index(drop=True)

    # -------- 4) Precompute CASE durations -----
    case_stats = (
        df.groupby("CASE ID")[["START TIME", "END TIME"]]
        .agg({"START TIME": "min", "END TIME": "max"})
        .reset_index()
    )
    case_stats["total_duration"] = (
        (case_stats["END TIME"] - case_stats["START TIME"])
        .dt.total_seconds()
        / 60
    )

    # -------- 5) Precompute ACTIVITY performance -----
    activity_perf = (
        df.groupby("EVENT")
        .agg(
            frequency=("EVENT", "count"),
            avg_duration=("EVENT_DURATION", "mean"),
            min_duration=("EVENT_DURATION", "min"),
            max_duration=("EVENT_DURATION", "max"),
        )
        .reset_index()
    )

    # -------- 6) Precompute PATH transitions (fast!) -----
    df["NEXT_EVENT"] = df.groupby("CASE ID")["EVENT"].shift(-1)
    df["NEXT_START"] = df.groupby("CASE ID")["START TIME"].shift(-1)

    transitions = df.dropna(subset=["NEXT_EVENT"]).copy()
    transitions["TRANSITION_DURATION"] = (
        transitions["NEXT_START"] - transitions["START TIME"]
    ).dt.total_seconds() / 60

    path_perf = (
        transitions.groupby(["EVENT", "NEXT_EVENT"])
        .agg(
            frequency=("EVENT", "count"),
            avg_duration=("TRANSITION_DURATION", "mean"),
        )
        .reset_index()
    ).rename(columns={"EVENT": "SOURCE", "NEXT_EVENT": "TARGET"})

    # ---------------------------------------------
    # RETURN the fully precomputed dataset
    # ---------------------------------------------
    return {
        "df": df,
        "case_stats": case_stats,
        "activity_perf": activity_perf,
        "path_perf": path_perf,
    }


# ==========================================================
# Load DF → from cache or MongoDB
# ==========================================================
def load_df(log_id):
    """Load preprocessed DF bundle from cache or MongoDB."""

    if hasattr(server, "LOG_STORE") and log_id in server.LOG_STORE:
        return server.LOG_STORE[log_id]["df"]

    # Load from DB
    db = server.db
    doc = db.event_logs.find_one({"_id": ObjectId(log_id)})

    if not doc:
        return None

    df = pd.DataFrame(doc["events"])

    processed = _preprocess_df(df)

    # Cache entire bundle
    if not hasattr(server, "LOG_STORE"):
        server.LOG_STORE = {}
    server.LOG_STORE[log_id] = processed

    return processed["df"]


def load_full_bundle(log_id):
    """Load the entire precomputed bundle: df, case stats, activity perf, path perf."""
    if hasattr(server, "LOG_STORE") and log_id in server.LOG_STORE:
        return server.LOG_STORE[log_id]

    # Otherwise load_df will populate LOG_STORE
    load_df(log_id)
    return server.LOG_STORE.get(log_id)



# ==========================================================
# Save new log → MongoDB + full preprocessing + cache
# ==========================================================
def save_log(df, filename):
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

    # Preprocess & Cache
    processed = _preprocess_df(df)

    if not hasattr(server, "LOG_STORE"):
        server.LOG_STORE = {}

    server.LOG_STORE[log_id] = processed

    return log_id


# ==========================================================
# Delete a log from MongoDB + remove cache
# ==========================================================
def delete_log(log_id):
    db = server.db
    db.event_logs.delete_one({"_id": ObjectId(log_id)})

    if hasattr(server, "LOG_STORE"):
        server.LOG_STORE.pop(log_id, None)


# ==========================================================
# List all uploaded logs
# ==========================================================
def list_logs():
    db = server.db
    return list(db.event_logs.find({}, {"filename": 1}))
