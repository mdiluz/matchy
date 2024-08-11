"""Utility functions for matchy"""
import logging
import random
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
import state


# Number of days to step forward from the start of history for each match attempt
_ATTEMPT_TIMESTEP_INCREMENT = timedelta(days=7)

# Attempts for each of those time periods
_ATTEMPTS_PER_TIMESTEP = 3

# Various eligability scoring factors for group meetups
_SCORE_CURRENT_MEMBERS = 2**1
_SCORE_REPEAT_ROLE = 2**2
_SCORE_REPEAT_MATCH = 2**3
_SCORE_EXTRA_MEMBERS = 2**4

# Scores higher than this are fully rejected
_SCORE_UPPER_THRESHOLD = 2**6

logger = logging.getLogger("matching")
logger.setLevel(logging.INFO)


@runtime_checkable
class Role(Protocol):
    @property
    def id(self) -> int:
        pass


@runtime_checkable
class Member(Protocol):
    @property
    def mention(self) -> str:
        pass

    @property
    def id(self) -> int:
        pass

    @property
    def roles(self) -> list[Role]:
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


def members_to_groups_simple(matchees: list[Member], per_group: int) -> tuple[bool, list[list[Member]]]:
    """Super simple group matching, literally no logic"""
    num_groups = max(len(matchees)//per_group, 1)
    return [matchees[i::num_groups] for i in range(num_groups)]


def get_member_group_eligibility_score(member: Member,
                                       group: list[Member],
                                       relevant_matches: list[int],
                                       per_group: int) -> int:
    """Rates a member against a group"""
    rating = len(group) * _SCORE_CURRENT_MEMBERS

    repeat_meetings = sum(m.id in relevant_matches for m in group)
    rating += repeat_meetings * _SCORE_REPEAT_MATCH

    repeat_roles = sum(r in member.roles for r in (m.roles for m in group))
    rating += (repeat_roles * _SCORE_REPEAT_ROLE)

    extra_members = len(group) - per_group
    if extra_members > 0:
        rating += extra_members * _SCORE_EXTRA_MEMBERS

    return rating


def attempt_create_groups(matchees: list[Member],
                          hist: state.State,
                          oldest_relevant_ts: datetime,
                          per_group: int) -> tuple[bool, list[list[Member]]]:
    """History aware group matching"""
    num_groups = max(len(matchees)//per_group, 1)

    # Set up the groups in place
    groups = list([] for _ in range(num_groups))

    matchees_left = matchees.copy()

    # Sequentially try and fit each matchee into a group
    while matchees_left:
        # Get the next matchee to place
        matchee = matchees_left.pop()
        matchee_matches = hist.matchees.get(
            str(matchee.id), {}).get("matches", {})
        relevant_matches = list(int(id) for id, ts in matchee_matches.items()
                                if state.ts_to_datetime(ts) >= oldest_relevant_ts)

        # Try every single group from the current group onwards
        # Progressing through the groups like this ensures we slowly fill them up with compatible people
        scores: list[tuple[int, int]] = []
        for group in groups:

            score = get_member_group_eligibility_score(
                matchee, group, relevant_matches, num_groups)

            # If the score isn't too high, consider this group
            if score <= _SCORE_UPPER_THRESHOLD:
                scores.append((group, score))

            # Optimisation:
            # A score of 0 means we've got something good enough and can skip
            if score == 0:
                break

        if scores:
            (group, _) = sorted(scores, key=lambda pair: pair[1])[0]
            group.append(matchee)
        else:
            # If we failed to add this matchee, bail on the group creation as it could not be done
            return None

    return groups


def datetime_range(start_time: datetime, increment: timedelta, end: datetime):
    """Yields a datetime range with a given increment"""
    current = start_time
    while current <= end or end is None:
        yield current
        current += increment


def members_to_groups(matchees: list[Member],
                      hist: state.State = state.State(),
                      per_group: int = 3,
                      allow_fallback: bool = False) -> list[list[Member]]:
    """Generate the groups from the set of matchees"""
    attempts = 0  # Tracking for logging purposes
    rand = random.Random(117)  # Some stable randomness

    # Grab the oldest timestamp
    history_start = hist.oldest_history() or datetime.now()

    # Walk from the start of time until now using the timestep increment
    for oldest_relevant_datetime in datetime_range(history_start, _ATTEMPT_TIMESTEP_INCREMENT, datetime.now()):

        # Have a few attempts before stepping forward in time
        for _ in range(_ATTEMPTS_PER_TIMESTEP):

            rand.shuffle(matchees)  # Shuffle the matchees each attempt

            attempts += 1
            groups = attempt_create_groups(
                matchees, hist, oldest_relevant_datetime, per_group)

            # Fail the match if our groups aren't big enough
            if (len(matchees)//per_group) <= 1 or (groups and all(len(g) >= per_group for g in groups)):
                logger.info("Matched groups after %s attempt(s)", attempts)
                return groups

    # If we've still failed, just use the simple method
    if allow_fallback:
        logger.info("Fell back to simple groups after %s attempt(s)", attempts)
        return members_to_groups_simple(matchees, per_group)


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
