"""Very simple config loading library"""
from schema import Schema, And, Use
import files
import os
import logging

logger = logging.getLogger("config")
logger.setLevel(logging.INFO)

_FILE = "config.json"

# Warning: Changing any of the below needs proper thought to ensure backwards compatibility
_VERSION = 1


class _Keys():
    TOKEN = "token"
    VERSION = "version"

    # Removed
    OWNERS = "owners"


_SCHEMA = Schema(
    {
        # The current version
        _Keys.VERSION: And(Use(int)),

        # Discord bot token
        _Keys.TOKEN: And(Use(str)),
    }
)


def _migrate_to_v1(d: dict):
    # Owners moved to History in v1
    # Note: owners will be required to be re-added to the state.json
    owners = d.pop(_Keys.OWNERS)
    logger.warn(
        "Migration removed owners from config, these must be re-added to the state.json")
    logger.warn("Owners: %s", owners)


# Set of migration functions to apply
_MIGRATIONS = [
    _migrate_to_v1
]


class Config():
    def __init__(self, data: dict):
        """Initialise and validate the config"""
        _SCHEMA.validate(data)
        self._dict = data

    @property
    def token(self) -> str:
        return self._dict["token"]


def _migrate(dict: dict):
    """Migrate a dict through versions"""
    version = dict.get("version", 0)
    for i in range(version, _VERSION):
        _MIGRATIONS[i](dict)
        dict["version"] = _VERSION


def load_from_file(file: str = _FILE) -> Config:
    """
    Load the state from a file
    Apply any required migrations
    """
    assert os.path.isfile(file)
    loaded = files.load(file)
    _migrate(loaded)
    return Config(loaded)
