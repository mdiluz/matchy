"""Very simple config loading library"""
from schema import Schema, Use, Optional
import files
import os
import logging

logger = logging.getLogger("config")
logger.setLevel(logging.INFO)

_FILE = "config.json"

# Warning: Changing any of the below needs proper thought to ensure backwards compatibility
_VERSION = 1


class _Key():
    TOKEN = "token"
    VERSION = "version"

    MATCH = "match"

    SCORE_FACTORS = "score_factors"
    REPEAT_ROLE = "repeat_role"
    REPEAT_MATCH = "repeat_match"
    EXTRA_MEMBER = "extra_member"
    UPPER_THRESHOLD = "upper_threshold"

    # Removed
    _OWNERS = "owners"


_SCHEMA = Schema(
    {
        # The current version
        _Key.VERSION: Use(int),

        # Discord bot token
        _Key.TOKEN: Use(str),

        # Settings for the match algorithmn, see matching.py for explanations on usage
        Optional(_Key.MATCH): {
            Optional(_Key.SCORE_FACTORS): {

                Optional(_Key.REPEAT_ROLE): Use(int),
                Optional(_Key.REPEAT_MATCH): Use(int),
                Optional(_Key.EXTRA_MEMBER): Use(int),
                Optional(_Key.UPPER_THRESHOLD): Use(int),
            }
        }
    }
)

_EMPTY_DICT = {
    _Key.TOKEN: "",
    _Key.VERSION: _VERSION
}


def _migrate_to_v1(d: dict):
    # Owners moved to History in v1
    # Note: owners will be required to be re-added to the state.json
    owners = d.pop(_Key._OWNERS)
    logger.warn(
        "Migration removed owners from config, these must be re-added to the state.json")
    logger.warn("Owners: %s", owners)


# Set of migration functions to apply
_MIGRATIONS = [
    _migrate_to_v1
]


class _ScoreFactors():
    def __init__(self, data: dict):
        """Initialise and validate the config"""
        self._dict = data

    @property
    def repeat_role(self) -> int:
        return self._dict.get(_Key.REPEAT_ROLE, None)

    @property
    def repeat_match(self) -> int:
        return self._dict.get(_Key.REPEAT_MATCH, None)

    @property
    def extra_member(self) -> int:
        return self._dict.get(_Key.EXTRA_MEMBER, None)

    @property
    def upper_threshold(self) -> int:
        return self._dict.get(_Key.UPPER_THRESHOLD, None)


class _Config():
    def __init__(self, data: dict):
        """Initialise and validate the config"""
        _SCHEMA.validate(data)
        self._dict = data

    @property
    def token(self) -> str:
        return self._dict["token"]

    @property
    def score_factors(self) -> _ScoreFactors:
        return _ScoreFactors(self._dict.get(_Key.SCORE_FACTORS, {}))


def _migrate(dict: dict):
    """Migrate a dict through versions"""
    version = dict.get("version", 0)
    for i in range(version, _VERSION):
        _MIGRATIONS[i](dict)
        dict["version"] = _VERSION


def _load_from_file(file: str = _FILE) -> _Config:
    """
    Load the state from a file
    Apply any required migrations
    """
    loaded = _EMPTY_DICT
    if os.path.isfile(file):
        loaded = files.load(file)
        _migrate(loaded)
    else:
        logger.warn("No %s file found, bot cannot run!", file)
    return _Config(loaded)


# Core config for users to use
# Singleton as there should only be one, and it's global
Config = _load_from_file()
