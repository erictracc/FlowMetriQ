# services/log_service.py

import pandas as pd
import numpy as np
from bson import ObjectId
from flask import current_app as server


# ==========================================================
# INTERNAL PREPROCESSOR
# Runs ONCE per uploaded log (heavy operations)
# ==========================================================
def _preprocess_df(df_raw: pd.DataFrame) -> dict:
    df = df_raw.copy()

    # ----- Datetime cleaning -----
    if "START TIME" in df:
        df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")

    if "END TIME" in df:
        df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")
    else:
        df["END TIME"] = df["START TIME"]

    # ----- Duration -----
    if "START TIME" in df and "END TIME" in df:
        df["EVENT_DURATION"] = (
            df["END TIME"] - df["START TIME"]
        ).dt.total_seconds() / 60.0
    else:
        df["EVENT_DURATION"] = np.nan

    # ----- Sort -----
    df = df.sort_values(["CASE ID", "START TIME"]).reset_index(drop=True)

    # ----- Case stats -----
    case_stats = (
        df.groupby("CASE ID")[["START TIME", "END TIME"]]
        .agg({"START TIME": "min", "END TIME": "max"})
        .reset_index()
    )
    case_stats["total_duration"] = (
        (case_stats["END TIME"] - case_stats["START TIME"])
        .dt.total_seconds() / 60.0
    )

    # ----- Activity performance -----
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

    # ----- Transitions -----
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
        .rename(columns={"EVENT": "SOURCE", "NEXT_EVENT": "TARGET"})
    )

    # ----- Return consistent bundle -----
    return {
        "df": df,
        "case_stats": case_stats,
        "activity_perf": activity_perf,
        "path_perf": path_perf,
    }


# ==========================================================
# SAFE LOAD FUNCTION — ALWAYS RETURNS A DATAFRAME
# ==========================================================
def load_df(log_id: str) -> pd.DataFrame:
    """
    ALWAYS returns a pandas DataFrame.
    Ensures pages never receive dicts accidentally.
    """

    # Create LOG_STORE if not exists
    if not hasattr(server, "LOG_STORE"):
        server.LOG_STORE = {}

    entry = server.LOG_STORE.get(log_id)

    # -------- Case 1: Proper cached bundle --------
    if isinstance(entry, dict) and "df" in entry:
        return entry["df"]

    # -------- Case 2: Someone accidentally cached df only --------
    if isinstance(entry, pd.DataFrame):
        # Fix the cache structure so this never happens again
        server.LOG_STORE[log_id] = {"df": entry}
        return entry

    # -------- Case 3: Some dict with unknown structure --------
    if isinstance(entry, dict):
        # Try to find a DataFrame inside
        for val in entry.values():
            if isinstance(val, pd.DataFrame):
                server.LOG_STORE[log_id] = {"df": val}
                return val

    # -------- Case 4: Not cached → Load from DB --------
    db = server.db
    doc = db.event_logs.find_one({"_id": ObjectId(log_id)})

    if not doc:
        print(f"[log_service] ERROR: Log {log_id} not found.")
        return pd.DataFrame()

    raw_df = pd.DataFrame(doc.get("events", []))

    # Ensure DF has CASE ID column
    if "CASE ID" not in raw_df:
        return pd.DataFrame()

    processed = _preprocess_df(raw_df)

    # Cache properly
    server.LOG_STORE[log_id] = processed

    return processed["df"]


# ==========================================================
# SAVE NEW LOG → DB + CACHE
# ==========================================================
def save_log(df: pd.DataFrame, filename: str) -> str:
    db = server.db

    log_doc = {
        "filename": filename,
        "columns": list(df.columns),
        "n_events": len(df),
        "n_cases": df["CASE ID"].nunique(),
        "events": df.to_dict("records"),
    }

    inserted = db.event_logs.insert_one(log_doc)
    log_id = str(inserted.inserted_id)

    processed = _preprocess_df(df)

    if not hasattr(server, "LOG_STORE"):
        server.LOG_STORE = {}

    server.LOG_STORE[log_id] = processed

    return log_id


# ==========================================================
# DELETE LOG
# ==========================================================
def delete_log(log_id: str):
    server.db.event_logs.delete_one({"_id": ObjectId(log_id)})

    if hasattr(server, "LOG_STORE"):
        server.LOG_STORE.pop(log_id, None)


# ==========================================================
# LIST LOGS (for dropdown)
# ==========================================================
def list_logs():
    return list(server.db.event_logs.find({}, {"filename": 1}))
