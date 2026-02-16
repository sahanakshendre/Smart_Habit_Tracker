import os
import json

DATA_FOLDER = "data"
FILE_PATH = os.path.join(DATA_FOLDER, "habits.json")


def initialize_storage():
    os.makedirs(DATA_FOLDER, exist_ok=True)

    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as f:
            json.dump([], f)


def load_habits():
    with open(FILE_PATH, "r") as f:
        return json.load(f)


def save_habits(habits):
    with open(FILE_PATH, "w") as f:
        json.dump(habits, f, indent=4)
