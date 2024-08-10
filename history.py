"""Store matching history"""
import os
import time
from schema import Schema, And, Use, Optional
from typing import Protocol
import matching

FILE = "history.json"


class Member(Protocol):
    @property
    def id(self) -> int:
        pass


class History():
    def __init__(self, data: dict):
        self.__dict__ = data

    @property
    def groups(self) -> list[dict]:
        return self.__dict__["groups"]

    @property
    def matchees(self) -> dict[str, dict]:
        return self.__dict__["matchees"]

    def save(self) -> None:
        """Save out the history"""
        matching.save(FILE, self.__dict__)

    def save_groups_to_history(self, groups: list[list[Member]]) -> None:
        """Save out the groups to the history file"""
        ts = time.time()
        for group in groups:
            # Add the group
            self.groups.append({
                "ts": ts,
                "matchees": list(m.id for m in group)
            })
            # Add the matches to the matchee data
            for m in group:
                matchee = self.matchees.get(str(m.id), {"matches": []})
                for o in (o for o in group if o.id != m.id):
                    matchee["matches"].append({"ts": ts, "id": o.id})
                self.matchees[str(m.id)] = matchee

        self.save()


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
