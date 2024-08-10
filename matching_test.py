"""
    Test functions for Matchy
"""
import discord
import pytest
import random
import matching
import history
from datetime import datetime, timedelta


def test_protocols():
    """Verify the protocols we're using match the discord ones"""
    assert isinstance(discord.Member, matching.Member)
    assert isinstance(discord.Guild, matching.Guild)
    assert isinstance(discord.Role, matching.Role)


class Member():
    def __init__(self, id: int):
        self._id = id

    @property
    def mention(self) -> str:
        return f"<@{self._id}>"

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value):
        self._id = value


def inner_validate_members_to_groups(matchees: list[Member], hist: history.History, per_group: int):
    """Inner function to validate the main output of the groups function"""
    groups = matching.members_to_groups(matchees, hist, per_group)

    # We should always have one group
    assert len(groups)

    # Log the groups to history
    # This will validate the internals
    hist.log_groups_to_history(groups)

    # Ensure each group contains within the bounds of expected members
    for group in groups:
        if len(matchees) >= per_group:
            assert len(group) >= per_group
        else:
            assert len(group) == len(matchees)
        assert len(group) < per_group*2  # TODO: We could be more strict here

    return groups


@pytest.mark.parametrize("matchees, per_group", [
    # Simplest test possible
    ([Member(1)], 1),

    # More requested than we have
    ([Member(1)], 2),

    # A selection of hyper-simple checks to validate core functionality
    ([Member(1)] * 100, 3),
    ([Member(1)] * 12, 5),
    ([Member(1)] * 11, 2),
    ([Member(1)] * 356, 8),
])
def test_members_to_groups_no_history(matchees, per_group):
    """Test simple group matching works"""
    hist = history.History()
    inner_validate_members_to_groups(matchees, hist, per_group)


def items_found_in_lists(list_of_lists, items):
    """validates if any sets of items are found in individual lists"""
    for sublist in list_of_lists:
        if all(item in sublist for item in items):
            return True
    return False


@pytest.mark.parametrize("history_data, matchees, per_group, checks", [
    # Slightly more difficult test
    # Describe a history where we previously matched up some people and ensure they don't get rematched
    (
        [
            {
                "ts": datetime.now() - timedelta(days=1),
                "groups": [
                    [Member(1), Member(2)],
                    [Member(3), Member(4)],
                ]
            }
        ],
        [
            Member(1),
            Member(2),
            Member(3),
            Member(4),
        ],
        2,
        [
            lambda groups: not items_found_in_lists(
                groups, [Member(1), Member(2)]),
            lambda groups: not items_found_in_lists(
                groups, [Member(3), Member(4)])
        ]
    ),
    # Feed the system an "impossible" test
    # The function should fall back to ignoring history and still give us something
    (
        [
            {
                "ts": datetime.now() - timedelta(days=1),
                "groups": [
                    [Member(1), Member(2), Member(3)],
                    [Member(4), Member(5), Member(6)],
                ]
            }
        ],
        [
            Member(1),
            Member(2),
            Member(3),
            Member(4),
            Member(5),
            Member(6),
        ],
        3,
        [
            # Nothing specific to validate
        ]
    ),
])
def test_members_to_groups_with_history(history_data, matchees, per_group, checks):
    """Test more advanced group matching works"""
    hist = history.History()

    # Replay the history
    for d in history_data:
        hist.log_groups_to_history(d["groups"], d["ts"])

    groups = inner_validate_members_to_groups(matchees, hist, per_group)

    # Run the custom validate functions
    for check in checks:
        assert check(groups)


def test_members_to_groups_stress_test():
    """stress test firing significant random data at the code"""

    # Use a stable rand, feel free to adjust this if needed but this lets the test be stable
    rand = random.Random(123)

    # Slowly ramp up the group size
    for per_group in range(1, 5):

        # Slowly ramp a randomized shuffled list of members
        for num_members in range(1, 5):
            # up to 50 total members
            matchees = list(Member(i)
                            for i in range(1, rand.randint(2, num_members*10 + 1)))
            rand.shuffle(matchees)

            for num_history in range(8):

                # Generate some super random history
                # Start some time from now to the past
                time = datetime.now() - timedelta(days=rand.randint(0, num_history*5))
                history_data = []
                for x in range(0, num_history):
                    run = {
                        "ts": time
                    }
                    groups = []
                    for y in range(1, num_history):
                        groups.append(list(Member(i)
                                           for i in range(1, max(num_members, rand.randint(2, num_members*10 + 1)))))
                    run["groups"] = groups
                    history_data.append(run)

                    # Step some time backwards in time
                    time -= timedelta(days=rand.randint(1, num_history))

                # No guarantees on history data order so make it a little harder for matchy
                rand.shuffle(history_data)

                # Replay the history
                hist = history.History()
                for d in history_data:
                    hist.log_groups_to_history(d["groups"], d["ts"])

                inner_validate_members_to_groups(matchees, hist, per_group)
