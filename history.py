"""Store matching history"""
import os
from schema import Schema, And, Use, Optional
import matching

FILE = "history.json"


class History():
    def __init__(self, data: dict):
        self.__dict__ = data

    @property
    def groups(self) -> list[dict]:
        return self.__dict__["groups"]

    @property
    def matchees(self) -> dict:
        return self.__dict__["matchees"]

    def save(self) -> None:
        """Save out the history"""
        matching.save(FILE, self.__dict__)


def load() -> History:
    """Load the history and validate it"""
    history = matching.load(FILE) if os.path.isfile(FILE) else {
        "groups": [],
        "matchees": {}
    }
    Schema(
        {
            Optional("groups"): [
                {
                    "ts": And(Use(str)),
                    "matchees": [
                        And(Use(int))
                    ]
                }
            ],
            Optional("matchees"): {
                Optional(str): {
                    "matches": [
                        {
                            "ts": And(Use(str)),
                            "id": And(Use(int)),
                        }
                    ]
                }

            }
        }
    ).validate(history)

    return History(history)
