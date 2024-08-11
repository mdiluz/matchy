"""Store bot state"""
import os
from datetime import datetime
from schema import Schema, And, Use, Optional
from typing import Protocol
import files
import copy
import logging

logger = logging.getLogger("state")
logger.setLevel(logging.INFO)


# Warning: Changing any of the below needs proper thought to ensure backwards compatibility
_VERSION = 1


def _migrate_to_v1(d: dict):
    logger.info("Renaming %s to %s", _Key.MATCHEES, _Key.USERS)
    d[_Key.USERS] = d[_Key.MATCHEES]
    del d[_Key.MATCHEES]


# Set of migration functions to apply
_MIGRATIONS = [
    _migrate_to_v1
]


class AuthScope(str):
    """Various auth scopes"""
    OWNER = "owner"
    MATCHER = "matcher"


class _Key(str):
    """Various keys used in the schema"""
    HISTORY = "history"
    GROUPS = "groups"
    MEMBERS = "members"
    USERS = "users"
    SCOPES = "scopes"
    MATCHES = "matches"
    ACTIVE = "active"
    CHANNELS = "channels"
    REACTIVATE = "reactivate"
    VERSION = "version"

    # Unused
    MATCHEES = "matchees"


_TIME_FORMAT = "%a %b %d %H:%M:%S %Y"


_SCHEMA = Schema(
    {
        # The current version
        _Key.VERSION: And(Use(int)),

        Optional(_Key.HISTORY): {
            # A datetime
            Optional(str): {
                _Key.GROUPS: [
                    {
                        _Key.MEMBERS: [
                            # The ID of each matchee in the match
                            And(Use(int))
                        ]
                    }
                ]
            }
        },
        Optional(_Key.USERS): {
            Optional(str): {
                Optional(_Key.SCOPES): And(Use(list[str])),
                Optional(_Key.MATCHES): {
                    # Matchee ID and Datetime pair
                    Optional(str): And(Use(str))
                },
                Optional(_Key.CHANNELS): {
                    # The channel ID
                    Optional(str): {
                        # Whether the user is signed up in this channel
                        _Key.ACTIVE: And(Use(bool)),
                    }
                }
            }
        },
    }
)

# Empty but schema-valid internal dict
_EMPTY_DICT = {
    _Key.HISTORY: {},
    _Key.USERS: {},
    _Key.VERSION: _VERSION
}
assert _SCHEMA.validate(_EMPTY_DICT)


class Member(Protocol):
    @property
    def id(self) -> int:
        pass


def ts_to_datetime(ts: str) -> datetime:
    """Convert a ts to datetime using the internal format"""
    return datetime.strptime(ts, _TIME_FORMAT)


class State():
    def __init__(self, data: dict = _EMPTY_DICT):
        """Initialise and validate the state"""
        self.validate(data)
        self._dict = copy.deepcopy(data)

    @property
    def _history(self) -> dict[str]:
        return self._dict[_Key.HISTORY]

    @property
    def _users(self) -> dict[str]:
        return self._dict[_Key.USERS]

    def validate(self, dict: dict = None):
        """Initialise and validate a state dict"""
        if not dict:
            dict = self._dict
        _SCHEMA.validate(dict)

    def get_oldest_timestamp(self) -> datetime:
        """Grab the oldest timestamp in history"""
        times = (ts_to_datetime(dt) for dt in self._history.keys())
        return next(times, None)

    def get_user_matches(self, id: int) -> list[int]:
        return self._users.get(str(id), {}).get(_Key.MATCHES, {})

    def log_groups(self, groups: list[list[Member]], ts: datetime = datetime.now()) -> None:
        """Log the groups"""
        tmp_state = State(self._dict)
        ts = datetime.strftime(ts, _TIME_FORMAT)

        # Grab or create the hitory item for this set of groups
        history_item = {}
        tmp_state._history[ts] = history_item
        history_item_groups = []
        history_item[_Key.GROUPS] = history_item_groups

        for group in groups:

            # Add the group data
            history_item_groups.append({
                _Key.MEMBERS: [m.id for m in group]
            })

            # Update the matchee data with the matches
            for m in group:
                matchee = tmp_state._users.get(str(m.id), {})
                matchee_matches = matchee.get(_Key.MATCHES, {})

                for o in (o for o in group if o.id != m.id):
                    matchee_matches[str(o.id)] = ts

                matchee[_Key.MATCHES] = matchee_matches
                tmp_state._users[str(m.id)] = matchee

        # Validate before storing the result
        tmp_state.validate()
        self._dict = tmp_state._dict

    def set_user_scope(self, id: str, scope: str, value: bool = True):
        """Add an auth scope to a user"""
        # Dive in
        user = self._users.get(str(id), {})
        scopes = user.get(_Key.SCOPES, [])

        # Set the value
        if value and scope not in scopes:
            scopes.append(scope)
        elif not value and scope in scopes:
            scopes.remove(scope)

        # Roll out
        user[_Key.SCOPES] = scopes
        self._users[id] = user

    def get_user_has_scope(self, id: str, scope: str) -> bool:
        """
            Check if a user has an auth scope
            "owner" users have all scopes
        """
        user = self._users.get(str(id), {})
        scopes = user.get(_Key.SCOPES, [])
        return AuthScope.OWNER in scopes or scope in scopes

    def set_use_active_in_channel(self, id: str, channel_id: str, active: bool = True):
        """Set a user as active (or not) on a given channel"""
        # Dive in
        user = self._users.get(str(id), {})
        channels = user.get(_Key.CHANNELS, {})
        channel = channels.get(str(channel_id), {})

        # Set the value
        channel[_Key.ACTIVE] = active

        # Unroll
        channels[str(channel_id)] = channel
        user[_Key.CHANNELS] = channels
        self._users[str(id)] = user

    def get_user_active_in_channel(self, id: str, channel_id: str) -> bool:
        """Get a users active channels"""
        user = self._users.get(str(id), {})
        channels = user.get(_Key.CHANNELS, {})
        return str(channel_id) in [channel for (channel, props) in channels.items() if props.get(_Key.ACTIVE, False)]

    @property
    def dict_internal(self) -> dict:
        """Only to be used to get the internal dict as a copy"""
        return copy.deepcopy(self._dict)


def _migrate(dict: dict):
    """Migrate a dict through versions"""
    version = dict.get("version", 0)
    for i in range(version, _VERSION):
        logger.info("Migrating from v%s to v%s", version, version+1)
        _MIGRATIONS[i](dict)
        dict[_Key.VERSION] = _VERSION


def load_from_file(file: str) -> State:
    """
    Load the state from a file
    Apply any required migrations
    """
    loaded = _EMPTY_DICT

    # If there's a file load it and try to migrate
    if os.path.isfile(file):
        loaded = files.load(file)
        _migrate(loaded)

    st = State(loaded)

    # Save out the migrated (or new) file
    files.save(file, st._dict)

    return st


def save_to_file(state: State, file: str):
    """Saves the state out to a file"""
    files.save(file, state.dict_internal)
