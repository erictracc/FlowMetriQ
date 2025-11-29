from .mongo import get_db

def ensure_collections(db):
    try:
        existing = db.list_collection_names()
        needed = ["event_logs", "users"]

        for name in needed:
            if name not in existing:
                db.create_collection(name)
                print(f"[MongoDB] Created collection → {name}")
            else:
                print(f"[MongoDB] Collection exists → {name}")

    except Exception as e:
        print(f"[MongoDB] ERROR ensuring collections → {e}")

