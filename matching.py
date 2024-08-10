"""Utility functions for matchy"""
import json
import random
from typing import Protocol


def load(file: str) -> dict:
    """Load a json file directly as a dict"""
    with open(file) as f:
        return json.load(f)


def save(file: str, content: dict):
    """Save out a content dictionary to a file"""
    with open(file, "w") as f:
        json.dump(content, f, indent=4)


def objects_to_groups(matchees: list[object],
                      per_group: int) -> list[list[object]]:
    """Generate the groups from the set of matchees"""
    random.shuffle(matchees)
    num_groups = max(len(matchees)//per_group, 1)
    return [matchees[i::num_groups] for i in range(num_groups)]


class Member(Protocol):
    """Protocol for the type of Member"""
    @property
    def mention(self) -> str:
        pass


def group_to_message(group: list[Member]) -> str:
    """Get the message to send for each group"""
    mentions = [m.mention for m in group]
    if len(group) > 1:
        mentions = f"{', '.join(mentions[:-1])} and {mentions[-1]}"
    else:
        mentions = mentions[0]
    return f"Matched up {mentions}!"


class Role(Protocol):
    @property
    def name(self) -> str:
        pass


class Guild(Protocol):
    @property
    def roles(self) -> list[Role]:
        pass


def get_role_from_guild(guild: Guild, role: str) -> Role:
    """Find a role in a guild"""
    return next((r for r in guild.roles if r.name == role), None)
