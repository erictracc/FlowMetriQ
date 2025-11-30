from flask import current_app as server
import pandas as pd
import uuid

def save_log_to_db(df, filename):
    """
    Stores a CSV event log in MongoDB.
    Returns the log_id (string).
    """
    log_id = str(uuid.uuid4())

    record = {
        "_id": log_id,
        "filename": filename,
        "data": df.to_dict("records"),
    }

    server.db["event_logs"].insert_one(record)
    return log_id


def load_log_from_db(log_id):
    """
    Retrieves a stored log from MongoDB and returns a pandas DataFrame.
    """
    record = server.db["event_logs"].find_one({"_id": log_id})
    if not record:
        return None

    return pd.DataFrame(record["data"])
