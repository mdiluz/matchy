"""File operation helpers"""
import json


def load(file: str) -> dict:
    """Load a json file directly as a dict"""
    with open(file) as f:
        return json.load(f)


def save(file: str, content: dict):
    """Save out a content dictionary to a file"""
    with open(file, "w") as f:
        json.dump(content, f, indent=4)
