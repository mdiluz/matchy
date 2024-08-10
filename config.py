"""Very simple config loading library"""
from schema import Schema, And, Use
import files

_FILE = "config.json"
_SCHEMA = Schema(
    {
        # Discord bot token
        "token": And(Use(str)),

        # ids of owners authorised to use owner-only commands
        "owners": And(Use(list[int])),
    }
)


class Config():
    def __init__(self, data: dict):
        """Initialise and validate the config"""
        _SCHEMA.validate(data)
        self.__dict__ = data

    @property
    def token(self) -> str:
        return self.__dict__["token"]

    @property
    def owners(self) -> list[int]:
        return self.__dict__["owners"]

    def reload(self) -> None:
        """Reload the config back into the dict"""
        self.__dict__ = load().__dict__


def load() -> Config:
    """Load the config"""
    return Config(files.load(_FILE))
