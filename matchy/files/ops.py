"""File operation helpers"""
import json
import shutil
import pathlib
import os


def load(file: str) -> dict:
    """Load a json file directly as a dict"""
    with open(file) as f:
        return json.load(f)


def save(file: str, content: dict):
    """
    Save out a content dictionary to a file
    """
    # Ensure the save directory exists first
    dir = pathlib.Path(os.path.dirname(file))
    dir.mkdir(parents=True, exist_ok=True)

    # Store in an intermediary directory first
    intermediate = file + ".nxt"
    with open(intermediate, "w") as f:
        json.dump(content, f, indent=4)
    shutil.move(intermediate, file)
