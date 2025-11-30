import pandas as pd
from bson import ObjectId
from flask import current_app as server


# ==========================================================
# Load DF → from cache or MongoDB
# ==========================================================
def load_df(log_id):
    """Load a dataframe either from in-memory cache or MongoDB."""

    # Check in-memory cache
    if hasattr(server, "LOG_STORE") and log_id in server.LOG_STORE:
        return server.LOG_STORE[log_id]

    # Fallback → MongoDB
    db = server.db
    doc = db.event_logs.find_one({"_id": ObjectId(log_id)})

    if not doc:
        return None

    df = pd.DataFrame(doc["events"])

    # Save to cache for faster DFG interactions
    if not hasattr(server, "LOG_STORE"):
        server.LOG_STORE = {}
    server.LOG_STORE[log_id] = df

    return df


# ==========================================================
# Save new log → MongoDB + cache
# ==========================================================
def save_log(df, filename):
    """Save a new uploaded event log to MongoDB + cache, return log_id."""

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

    # Cache it
    if not hasattr(server, "LOG_STORE"):
        server.LOG_STORE = {}
    server.LOG_STORE[log_id] = df

    return log_id


# ==========================================================
# Delete a log from MongoDB + remove cache
# ==========================================================
def delete_log(log_id):
    """Delete a log from MongoDB and clear cache."""

    db = server.db
    db.event_logs.delete_one({"_id": ObjectId(log_id)})

    if hasattr(server, "LOG_STORE"):
        server.LOG_STORE.pop(log_id, None)


# ==========================================================
# List all uploaded logs
# ==========================================================
def list_logs():
    """Return all logs stored in MongoDB as a simple list."""

    db = server.db
    return list(db.event_logs.find({}, {"filename": 1}))
