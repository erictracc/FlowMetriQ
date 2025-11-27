import json
import os

CONFIG_PATH = "config/settings.json"

def load_settings():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_settings(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)
