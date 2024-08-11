"""Utility functions for matchy"""
import logging
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
import state


# Number of days to step forward from the start of history for each match attempt
_ATTEMPT_TIMESTEP_INCREMENT = timedelta(days=7)


class _ScoreFactors(int):
    """Various eligability scoring factors for group meetups"""
    REPEAT_ROLE = 2**2
    REPEAT_MATCH = 2**3
    EXTRA_MEMBER = 2**5

    # Scores higher than this are fully rejected
    UPPER_THRESHOLD = 2**6


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
                                       prior_matches: list[int],
                                       per_group: int) -> float:
    """Rates a member against a group"""
    # An empty group is a "perfect" score atomatically
    rating = 0
    if not group:
        return rating

    # Add score based on prior matchups of this user
    rating += sum(m.id in prior_matches for m in group) * \
        _ScoreFactors.REPEAT_MATCH

    # Calculate the number of roles that match
    all_role_ids = set(r.id for mr in [r.roles for r in group] for r in mr)
    member_role_ids = [r.id for r in member.roles]
    repeat_roles = sum(id in member_role_ids for id in all_role_ids)
    rating += repeat_roles * _ScoreFactors.REPEAT_ROLE

    # Add score based on the number of extra members
    # Calculate the member offset (+1 for this user)
    extra_members = (len(group) - per_group) + 1
    if extra_members >= 0:
        rating += extra_members * _ScoreFactors.EXTRA_MEMBER

    return rating


def attempt_create_groups(matchees: list[Member],
                          current_state: state.State,
                          oldest_relevant_ts: datetime,
                          per_group: int) -> tuple[bool, list[list[Member]]]:
    """History aware group matching"""
    num_groups = max(len(matchees)//per_group, 1)

    # Set up the groups in place
    groups = [[] for _ in range(num_groups)]

    matchees_left = matchees.copy()

    # Sequentially try and fit each matchee into a group
    while matchees_left:
        # Get the next matchee to place
        matchee = matchees_left.pop()
        matchee_matches = current_state.get_user_matches(matchee.id)
        relevant_matches = [int(id) for id, ts
                            in matchee_matches.items()
                            if state.ts_to_datetime(ts) >= oldest_relevant_ts]

        # Try every single group from the current group onwards
        # Progressing through the groups like this ensures we slowly fill them up with compatible people
        scores: list[tuple[int, float]] = []
        for group in groups:

            score = get_member_group_eligibility_score(
                matchee, group, relevant_matches, per_group)

            # If the score isn't too high, consider this group
            if score <= _ScoreFactors.UPPER_THRESHOLD:
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


def iterate_all_shifts(list: list):
    """Yields each shifted variation of the input list"""
    yield list
    for _ in range(len(list)-1):
        list = list[1:] + [list[0]]
        yield list


def members_to_groups(matchees: list[Member],
                      hist: state.State = state.State(),
                      per_group: int = 3,
                      allow_fallback: bool = False) -> list[list[Member]]:
    """Generate the groups from the set of matchees"""
    attempts = 0  # Tracking for logging purposes
    num_groups = len(matchees)//per_group

    # Bail early if there's no-one to match
    if not matchees:
        return []

    # Grab the oldest timestamp
    history_start = hist.get_oldest_timestamp() or datetime.now()

    # Walk from the start of time until now using the timestep increment
    for oldest_relevant_datetime in datetime_range(history_start, _ATTEMPT_TIMESTEP_INCREMENT, datetime.now()):

        # Attempt with each starting matchee
        for shifted_matchees in iterate_all_shifts(matchees):

            attempts += 1
            groups = attempt_create_groups(
                shifted_matchees, hist, oldest_relevant_datetime, per_group)

            # Fail the match if our groups aren't big enough
            if num_groups <= 1 or (groups and all(len(g) >= per_group for g in groups)):
                logger.info("Matched groups after %s attempt(s)", attempts)
                return groups

    # If we've still failed, just use the simple method
    if allow_fallback:
        logger.info("Fell back to simple groups after %s attempt(s)", attempts)
        return members_to_groups_simple(matchees, per_group)

    # Simply assert false, this should never happen
    # And should be caught by tests
    assert False


def group_to_message(group: list[Member]) -> str:
    """Get the message to send for each group"""
    mentions = [m.mention for m in group]
    if len(group) > 1:
        mentions = f"{', '.join(mentions[:-1])} and {mentions[-1]}"
    else:
        mentions = mentions[0]
    return f"Matched up {mentions}!"
