"""Store bot state"""
import os
from datetime import datetime
from schema import Schema, And, Use, Optional
from typing import Protocol
import files
import copy

_FILE = "state.json"

# Warning: Changing any of the below needs proper thought to ensure backwards compatibility
_DEFAULT_DICT = {
    "history": {},
    "matchees": {}
}
_TIME_FORMAT = "%a %b %d %H:%M:%S %Y"
_SCHEMA = Schema(
    {
        Optional("history"): {
            Optional(str): {  # a datetime
                "groups": [
                    {
                        "members": [
                            # The ID of each matchee in the match
                            And(Use(int))
                        ]
                    }
                ]
            }
        },
        Optional("matchees"): {
            Optional(str): {
                Optional("matches"): {
                    # Matchee ID and Datetime pair
                    Optional(str): And(Use(str))
                }
            }
        }
    }
)


class Member(Protocol):
    @property
    def id(self) -> int:
        pass


def ts_to_datetime(ts: str) -> datetime:
    """Convert a ts to datetime using the internal format"""
    return datetime.strptime(ts, _TIME_FORMAT)


def validate(dict: dict):
    """Initialise and validate the state"""
    _SCHEMA.validate(dict)


class State():
    def __init__(self, data: dict = _DEFAULT_DICT):
        """Initialise and validate the state"""
        validate(data)
        self.__dict__ = copy.deepcopy(data)

    @property
    def history(self) -> list[dict]:
        return self.__dict__["history"]

    @property
    def matchees(self) -> dict[str, dict]:
        return self.__dict__["matchees"]

    def save(self) -> None:
        """Save out the state"""
        files.save(_FILE, self.__dict__)

    def oldest_history(self) -> datetime:
        """Grab the oldest timestamp in history"""
        if not self.history:
            return None
        times = (ts_to_datetime(dt) for dt in self.history.keys())
        return sorted(times)[0]

    def log_groups(self, groups: list[list[Member]], ts: datetime = datetime.now()) -> None:
        """Log the groups"""
        tmp_state = State(self.__dict__)
        ts = datetime.strftime(ts, _TIME_FORMAT)

        # Grab or create the hitory item for this set of groups
        history_item = {}
        tmp_state.history[ts] = history_item
        history_item_groups = []
        history_item["groups"] = history_item_groups

        for group in groups:

            # Add the group data
            history_item_groups.append({
                "members": list(m.id for m in group)
            })

            # Update the matchee data with the matches
            for m in group:
                matchee = tmp_state.matchees.get(str(m.id), {})
                matchee_matches = matchee.get("matches", {})

                for o in (o for o in group if o.id != m.id):
                    matchee_matches[str(o.id)] = ts

                matchee["matches"] = matchee_matches
                tmp_state.matchees[str(m.id)] = matchee

        # Validate before storing the result
        validate(self.__dict__)
        self.__dict__ = tmp_state.__dict__

    def save_groups(self, groups: list[list[Member]]) -> None:
        """Save out the groups to the state file"""
        self.log_groups(groups)
        self.save()


def load() -> State:
    """Load the state"""
    return State(files.load(_FILE) if os.path.isfile(_FILE) else _DEFAULT_DICT)
