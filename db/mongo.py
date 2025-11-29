# flowmetriq/db/mongo.py
import json
from pymongo import MongoClient
from bson.json_util import dumps
import os

# Load settings from config/settings.json
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")

with open(CONFIG_PATH, "r") as f:
    settings = json.load(f)

MONGO_URI = settings.get("database_uri")
DB_NAME = settings.get("database_name", "flowmetriqdb")

_client = None
_db = None


def get_db():
    """Return a persistent MongoDB database connection.
       Equivalent to ensureMongoConnection in Node.js."""
    global _client, _db

    if _db is not None:
        return _db

    # Otherwise connect now
    _client = MongoClient(MONGO_URI)
    _db = _client[DB_NAME]

    print(f"[MongoDB] Connected → {MONGO_URI} / {DB_NAME}")
    return _db
