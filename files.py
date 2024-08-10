"""File operation helpers"""
import json
import shutil


def load(file: str) -> dict:
    """Load a json file directly as a dict"""
    with open(file) as f:
        return json.load(f)


def save(file: str, content: dict):
    """
    Save out a content dictionary to a file
    Stores it in an intermediary file first incase the dump fails
    """
    intermediate = file + ".nxt"
    with open(intermediate, "w") as f:
        json.dump(content, f, indent=4)
    shutil.move(intermediate, file)
