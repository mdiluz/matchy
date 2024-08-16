"""Store bot state"""
import os
from datetime import datetime
from schema import Schema, Use, Optional
from collections.abc import Generator
from typing import Protocol
import matchy.files.ops as ops
import copy
import logging
from functools import wraps

logger = logging.getLogger("state")
logger.setLevel(logging.INFO)


# Warning: Changing any of the below needs proper thought to ensure backwards compatibility
_VERSION = 4


def _migrate_to_v1(d: dict):
    """v1 simply renamed matchees to users"""
    logger.info("Renaming %s to %s", _Key._MATCHEES, _Key.USERS)
    d[_Key.USERS] = d[_Key._MATCHEES]
    del d[_Key._MATCHEES]


def _migrate_to_v2(d: dict):
    """v2 swapped the date over to a less silly format"""
    logger.info("Fixing up date format from %s to %s",
                _TIME_FORMAT_OLD, _TIME_FORMAT)

    def old_to_new_ts(ts: str) -> str:
        return datetime.strftime(datetime.strptime(ts, _TIME_FORMAT_OLD), _TIME_FORMAT)

    # Adjust all the history keys
    d[_Key._HISTORY] = {
        old_to_new_ts(ts): entry
        for ts, entry in d[_Key._HISTORY].items()
    }
    # Adjust all the user parts
    for user in d[_Key.USERS].values():
        # Update the match dates
        matches = user.get(_Key.MATCHES, {})
        for id, ts in matches.items():
            matches[id] = old_to_new_ts(ts)

        # Update any reactivation dates
        channels = user.get(_Key.CHANNELS, {})
        for id, channel in channels.items():
            old_ts = channel.get(_Key.REACTIVATE, None)
            if old_ts:
                channel[_Key.REACTIVATE] = old_to_new_ts(old_ts)


def _migrate_to_v3(d: dict):
    """v3 simply added the tasks entry"""
    d[_Key.TASKS] = {}


def _migrate_to_v4(d: dict):
    """v4 removed verbose history tracking"""
    del d[_Key._HISTORY]


# Set of migration functions to apply
_MIGRATIONS = [
    _migrate_to_v1,
    _migrate_to_v2,
    _migrate_to_v3,
    _migrate_to_v4,
]


class AuthScope(str):
    """Various auth scopes"""
    MATCHER = "matcher"


class _Key(str):
    """Various keys used in the schema"""
    VERSION = "version"

    USERS = "users"
    SCOPES = "scopes"
    MATCHES = "matches"
    ACTIVE = "active"
    CHANNELS = "channels"
    REACTIVATE = "reactivate"

    TASKS = "tasks"
    MATCH_TASKS = "match_tasks"
    MEMBERS_MIN = "members_min"
    WEEKDAY = "weekdays"
    HOUR = "hours"

    # Unused
    _MATCHEES = "matchees"
    _HISTORY = "history"
    _GROUPS = "groups"
    _MEMBERS = "members"


_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
_TIME_FORMAT_OLD = "%a %b %d %H:%M:%S %Y"


_SCHEMA = Schema(
    {
        # The current version
        _Key.VERSION: Use(int),

        _Key.USERS: {
            # User ID as string
            Optional(str): {
                Optional(_Key.SCOPES): Use(list[str]),
                Optional(_Key.MATCHES): {
                    # Matchee ID and Datetime pair
                    Optional(str): Use(str)
                },
                Optional(_Key.CHANNELS): {
                    # The channel ID
                    Optional(str): {
                        # Whether the user is signed up in this channel
                        _Key.ACTIVE: Use(bool),
                        # A timestamp for when to re-activate the user
                        Optional(_Key.REACTIVATE): Use(str),
                    }
                }
            }
        },

        _Key.TASKS: {
            # Channel ID as string
            Optional(str): {
                Optional(_Key.MATCH_TASKS): [
                    {
                        _Key.MEMBERS_MIN: Use(int),
                        _Key.WEEKDAY: Use(int),
                        _Key.HOUR: Use(int),
                    }
                ]
            }
        }
    }
)

# Empty but schema-valid internal dict
_EMPTY_DICT = {
    _Key.USERS: {},
    _Key.TASKS: {},
    _Key.VERSION: _VERSION
}
assert _SCHEMA.validate(_EMPTY_DICT)


class Member(Protocol):
    @property
    def id(self) -> int:
        pass


def ts_to_datetime(ts: str) -> datetime:
    """Convert a string ts to datetime using the internal format"""
    return datetime.strptime(ts, _TIME_FORMAT)


def datetime_to_ts(ts: datetime) -> str:
    """Convert a datetime to a string ts using the internal format"""
    return datetime.strftime(ts, _TIME_FORMAT)


class State():
    def __init__(self, data: dict, file: str | None = None):
        """Copy the data, migrate if needed, and validate"""
        self._dict = copy.deepcopy(data)
        self._file = file

        version = self._dict.get("version", 0)
        for i in range(version, _VERSION):
            logger.info("Migrating from v%s to v%s", version, version+1)
            _MIGRATIONS[i](self._dict)
            self._dict[_Key.VERSION] = _VERSION

        _SCHEMA.validate(self._dict)

    @staticmethod
    def safe_write(func):
        """
        Wraps any function running it first on some temporary state
        Validates the resulting state and only then attempts to save it out
        before storing the dict back in the State
        """
        @wraps(func)
        def inner(self: State, *args, **kwargs):
            tmp = State(self._dict, self._file)
            func(tmp, *args, **kwargs)
            _SCHEMA.validate(tmp._dict)
            if tmp._file:
                ops.save(tmp._file, tmp._dict)
            self._dict = tmp._dict

        return inner

    def get_history_timestamps(self, users: list[Member]) -> list[datetime]:
        """Grab all timestamps in the history"""
        others = [m.id for m in users]

        # Fetch all the interaction times in history
        # But only for interactions in the given user group
        times = set()
        for data in (data for id, data in self._users.items() if int(id) in others):
            matches = data.get(_Key.MATCHES, {})
            for ts in (ts for id, ts in matches.items() if int(id) in others):
                times.add(ts)

        # Convert to datetimes and sort
        datetimes = [ts_to_datetime(ts) for ts in times]
        datetimes.sort()
        return datetimes

    def get_user_matches(self, id: int) -> list[int]:
        return self._users.get(str(id), {}).get(_Key.MATCHES, {})

    @safe_write
    def log_groups(self, groups: list[list[Member]], ts: datetime = None) -> None:
        """Log the groups"""
        ts = datetime_to_ts(ts or datetime.now())
        for group in groups:
            # Update the matchee data with the matches
            for m in group:
                matchee = self._users.setdefault(str(m.id), {})
                matchee_matches = matchee.setdefault(_Key.MATCHES, {})

                for o in (o for o in group if o.id != m.id):
                    matchee_matches[str(o.id)] = ts

    @safe_write
    def set_user_scope(self, id: str, scope: str, value: bool = True):
        """Add an auth scope to a user"""
        # Dive in
        user = self._users.setdefault(str(id), {})
        scopes = user.setdefault(_Key.SCOPES, [])

        # Set the value
        if value and scope not in scopes:
            scopes.append(scope)
        elif not value and scope in scopes:
            scopes.remove(scope)

    def get_user_has_scope(self, id: str, scope: str) -> bool:
        """
            Check if a user has an auth scope
            "owner" users have all scopes
        """
        user = self._users.get(str(id), {})
        scopes = user.get(_Key.SCOPES, [])
        return scope in scopes

    def set_user_active_in_channel(self, id: str, channel_id: str, active: bool = True):
        """Set a user as active (or not) on a given channel"""
        self._set_user_channel_prop(id, channel_id, _Key.ACTIVE, active)

    def get_user_active_in_channel(self, id: str, channel_id: str) -> bool:
        """Get a users active channels"""
        user = self._users.get(str(id), {})
        channels = user.get(_Key.CHANNELS, {})
        return str(channel_id) in [channel for (channel, props) in channels.items() if props.get(_Key.ACTIVE, False)]

    def set_user_paused_in_channel(self, id: str, channel_id: str, until: datetime):
        """Sets a user as paused in a channel"""
        # Deactivate the user in the channel first
        self.set_user_active_in_channel(id, channel_id, False)

        self._set_user_channel_prop(
            id, channel_id, _Key.REACTIVATE, datetime_to_ts(until))

    @safe_write
    def reactivate_users(self, channel_id: str):
        """Reactivate any users who've passed their reactivation time on this channel"""
        for user in self._users.values():
            channels = user.get(_Key.CHANNELS, {})
            channel = channels.get(str(channel_id), {})
            if channel and not channel[_Key.ACTIVE]:
                reactivate = channel.get(_Key.REACTIVATE, None)
                # Check if we've gone past the reactivation time and re-activate
                if reactivate and datetime.now() > ts_to_datetime(reactivate):
                    channel[_Key.ACTIVE] = True

    def get_active_match_tasks(self, time: datetime | None = None) -> Generator[str, int]:
        """
        Get any active match tasks at the given time
        returns list of channel,members_min pairs
        """
        if not time:
            time = datetime.now()
        weekday = time.weekday()
        hour = time.hour

        for channel, tasks in self._tasks.items():
            for match in tasks.get(_Key.MATCH_TASKS, []):
                if match[_Key.WEEKDAY] == weekday and match[_Key.HOUR] == hour:
                    yield (channel, match[_Key.MEMBERS_MIN])

    def get_channel_match_tasks(self, channel_id: str) -> Generator[int, int, int]:
        """
        Get all match tasks for the channel
        """
        all_tasks = (
            tasks.get(_Key.MATCH_TASKS, [])
            for channel, tasks in self._tasks.items()
            if str(channel) == str(channel_id)
        )
        for tasks in all_tasks:
            for task in tasks:
                yield (task[_Key.WEEKDAY], task[_Key.HOUR], task[_Key.MEMBERS_MIN])

    @safe_write
    def set_channel_match_task(self, channel_id: str, members_min: int, weekday: int, hour: int, set: bool) -> bool:
        """Set up a match task on a channel"""
        channel = self._tasks.setdefault(str(channel_id), {})
        matches = channel.setdefault(_Key.MATCH_TASKS, [])

        found = False
        for match in matches:
            # Specifically check for the combination of weekday and hour
            if match[_Key.WEEKDAY] == weekday and match[_Key.HOUR] == hour:
                found = True
                if set:
                    match[_Key.MEMBERS_MIN] = members_min
                else:
                    matches.remove(match)

                # Return true as we've successfully changed the data in place
                return True

        # If we didn't find it, add it to the schedule
        if not found and set:
            matches.append({
                _Key.MEMBERS_MIN: members_min,
                _Key.WEEKDAY: weekday,
                _Key.HOUR: hour,
            })

            return True

        # We did not manage to remove the schedule (or add it? though that should be impossible)
        return False

    @property
    def _users(self) -> dict[str]:
        return self._dict[_Key.USERS]

    @property
    def _tasks(self) -> dict[str]:
        return self._dict[_Key.TASKS]

    @safe_write
    def _set_user_channel_prop(self, id: str, channel_id: str, key: str, value):
        """Set a user channel property helper"""
        user = self._users.setdefault(str(id), {})
        channels = user.setdefault(_Key.CHANNELS, {})
        channel = channels.setdefault(str(channel_id), {})
        channel[key] = value


def load_from_file(file: str) -> State:
    """
    Load the state from a files
    """
    loaded = ops.load(file) if os.path.isfile(file) else _EMPTY_DICT
    st = State(loaded, file)
    ops.save(file, st._dict)
    return st
