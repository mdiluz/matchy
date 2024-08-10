"""Very simple config loading library"""
import json

CONFIG = "config.json"


def load() -> dict:
    with open(CONFIG) as f:
        return json.load(f)
