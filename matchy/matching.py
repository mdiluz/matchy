"""Utility functions for matchy"""
import logging
import discord
from datetime import datetime
from typing import Protocol, runtime_checkable
from matchy.files.state import State, ts_to_datetime
import matchy.util as util


class _ScoreFactors(int):
    """
    Score factors used when trying to build up "best fit" groups
    Matchees are sequentially placed into the lowest scoring available group
    """

    # Added for each role the matchee has that another group member has
    REPEAT_ROLE = 2**2
    # Added for each member in the group that the matchee has already matched with
    REPEAT_MATCH = 2**3
    # Added for each additional member over the set "per group" value
    EXTRA_MEMBER = 2**5

    # Upper threshold, if the user scores higher than this they will not be placed in that group
    UPPER_THRESHOLD = 2**6


logger = logging.getLogger("matching")
logger.setLevel(logging.INFO)


@runtime_checkable
class Role(Protocol):
    @property
    def id(self) -> int:
        pass

    @property
    def name(self) -> str:
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
    def display_name(self) -> str:
        pass

    @property
    def roles(self) -> list[Role]:
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
    num_prior = sum(m.id in prior_matches for m in group)
    rating += num_prior * _ScoreFactors.REPEAT_MATCH

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
                          state: State,
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
        matchee_matches = state.get_user_matches(matchee.id)
        relevant_matches = [int(id) for id, ts
                            in matchee_matches.items()
                            if ts_to_datetime(ts) >= oldest_relevant_ts]

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


def iterate_all_shifts(list: list):
    """Yields each shifted variation of the input list"""
    yield list
    for _ in range(len(list)-1):
        list = list[1:] + [list[0]]
        yield list


def members_to_groups(matchees: list[Member],
                      state: State,
                      per_group: int = 3,
                      allow_fallback: bool = False) -> list[list[Member]]:
    """Generate the groups from the set of matchees"""
    attempts = 0  # Tracking for logging purposes
    num_groups = len(matchees)//per_group

    # Bail early if there's no-one to match
    if not matchees:
        return []

    # Walk from the start of history until now trying to match up groups
    for oldest_relevant_datetime in state.get_history_timestamps(matchees) + [datetime.now()]:

        # Attempt with each starting matchee
        for shifted_matchees in iterate_all_shifts(matchees):

            attempts += 1
            groups = attempt_create_groups(
                shifted_matchees, state, oldest_relevant_datetime, per_group)

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


async def match_groups_in_channel(state: State, channel: discord.channel, min: int):
    """Match up the groups in a given channel"""
    groups = active_members_to_groups(state, channel, min)

    # Send the groups
    for group in groups:

        message = await channel.send(
            f"Matched up {util.format_list([m.mention for m in group])}!")

        # Set up a thread for this match if the bot has permissions to do so
        if channel.permissions_for(channel.guild.me).create_public_threads:
            await channel.create_thread(
                name=util.format_list([m.display_name for m in group]),
                message=message,
                reason="Creating a matching thread")

    # Close off with a message
    await channel.send("That's all folks, happy matching and remember - DFTBA!")

    # Save the groups to the history
    state.log_groups(groups)

    logger.info("Done! Matched into %s groups.", len(groups))


def get_matchees_in_channel(state: State, channel: discord.channel):
    """Fetches the matchees in a channel"""
    # Reactivate any unpaused users
    state.reactivate_users(channel.id)

    # Gather up the prospective matchees
    return [m for m in channel.members if state.get_user_active_in_channel(m.id, channel.id)]


def active_members_to_groups(state: State, channel: discord.channel, min_members: int):
    """Helper to create groups from channel members"""

    # Gather up the prospective matchees
    matchees = get_matchees_in_channel(state, channel)

    # Create our groups!
    return members_to_groups(matchees, state, min_members, allow_fallback=True)
