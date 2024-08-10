"""Utility functions for matchy"""
import random
from typing import Protocol


class Member(Protocol):
    @property
    def id(self) -> int:
        pass


def members_to_groups(matchees: list[Member],
                      per_group: int) -> list[list[Member]]:
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
