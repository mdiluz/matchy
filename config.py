"""Very simple config loading library"""
from schema import Schema, And, Use
import matching

CONFIG = "config.json"


class Config():
    def __init__(self, data: dict):
        self.__dict__ = data

    @property
    def token(self) -> str:
        return self.__dict__["token"]

    @property
    def owners(self) -> list[int]:
        return self.__dict__["owners"]


def load() -> Config:
    """Load the config and validate it"""
    config = matching.load(CONFIG)
    Schema(
        {
            # Discord bot token
            "token": And(Use(str)),

            # ids of owners authorised to use owner-only commands
            "owners": And(Use(list[int])),
        }
    ).validate(config)

    return Config(config)
