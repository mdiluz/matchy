"""Utility functions for matchy"""
import logging
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
import history


# Number of days to step forward from the start of history for each match attempt
_ATTEMPT_RELEVANCY_TIMESTEP = timedelta(days=7)

# Attempts for each of those time periods
_ATTEMPTS_PER_TIMESTEP = 3

logger = logging.getLogger("matching")
logger.setLevel(logging.INFO)


@runtime_checkable
class Member(Protocol):
    @property
    def mention(self) -> str:
        pass

    @property
    def id(self) -> int:
        pass


@runtime_checkable
class Role(Protocol):
    @property
    def name(self) -> str:
        pass


@runtime_checkable
class Guild(Protocol):
    @property
    def roles(self) -> list[Role]:
        pass


def members_to_groups_simple(matchees: list[Member], num_groups: int) -> tuple[bool, list[list[Member]]]:
    """Super simple group matching, literally no logic"""
    return [matchees[i::num_groups] for i in range(num_groups)]


def circular_iterator(lst, start_index):
    for i in range(start_index, len(lst)):
        yield i, lst[i]
    for i in range(0, start_index):
        yield i, lst[i]


def attempt_create_groups(matchees: list[Member],
                          hist: history.History,
                          oldest_relevant_ts: datetime,
                          num_groups: int) -> tuple[bool, list[list[Member]]]:
    """History aware group matching"""

    # Set up the groups in place
    groups = list([] for _ in range(num_groups))

    matchees_left = matchees.copy()

    # Sequentially try and fit each matchy into groups one by one
    current_group = 0
    while matchees_left:
        # Get the next matchee to place
        matchee = matchees_left.pop()
        matchee_matches = hist.matchees.get(
            str(matchee.id), {}).get("matches", {})
        relevant_matches = list(int(id) for id, ts in matchee_matches.items()
                                if history.ts_to_datetime(ts) >= oldest_relevant_ts)

        # Try every single group from the current group onwards
        # Progressing through the groups like this ensures we slowly fill them up with compatible people
        added = False
        for idx, group in circular_iterator(groups, current_group):
            current_group = idx  # Track the current group

            # Current compatibilty is simply whether or not the group has any members with previous matches in it
            if not any(m.id in relevant_matches for m in group):
                group.append(matchee)
                added = True
                break

        # If we failed to add this matchee, bail on the group creation as it could not be done
        if not added:
            return None

        # Move on to the next group
        current_group += 1
        if current_group >= len(groups):
            current_group = 0

    return groups


def members_to_groups(matchees: list[Member],
                      hist: history.History = history.History(),
                      per_group: int = 3) -> list[list[Member]]:
    """Generate the groups from the set of matchees"""
    num_groups = max(len(matchees)//per_group, 1)

    # Only both with the complicated matching if we have a history
    # TODO: When matching takes into account more than history this should change
    if not hist.history:
        logger.info("No history so matched groups with simple method")
        return members_to_groups_simple(matchees, num_groups)

    # Grab the oldest timestamp
    oldest_relevant_datetime = hist.oldest()

    # Loop until we find a valid set of groups
    attempts = 0
    while True:
        attempts += 1

        groups = attempt_create_groups(
            matchees, hist, oldest_relevant_datetime, num_groups)

        # Fail the match if our groups aren't big enough
        if groups and all(len(g) > per_group for g in groups):
            logger.info("Matched groups after %s attempt(s)", attempts)
            return groups

        # In case we still don't have groups we should progress and
        # walk the oldest relevant timestamp forward a week
        # Stop bothering when we finally go beyond today
        if attempts % _ATTEMPTS_PER_TIMESTEP == 0:
            oldest_relevant_datetime += _ATTEMPT_RELEVANCY_TIMESTEP
            if oldest_relevant_datetime > datetime.now():
                break

    # If we've still failed, just use the simple method
    logger.info("Fell back to simple groups after %s attempt(s)", attempts)
    return members_to_groups_simple(matchees, num_groups)


def group_to_message(group: list[Member]) -> str:
    """Get the message to send for each group"""
    mentions = [m.mention for m in group]
    if len(group) > 1:
        mentions = f"{', '.join(mentions[:-1])} and {mentions[-1]}"
    else:
        mentions = mentions[0]
    return f"Matched up {mentions}!"


def get_role_from_guild(guild: Guild, role: str) -> Role:
    """Find a role in a guild"""
    return next((r for r in guild.roles if r.name == role), None)
