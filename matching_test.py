"""
    Test functions for Matchy
"""
import discord
import pytest
import matching
import history
from datetime import datetime, timedelta


def test_protocols():
    """Verify the protocols we're using match the discord ones"""
    assert isinstance(discord.Member, matching.Member)
    assert isinstance(discord.Guild, matching.Guild)
    assert isinstance(discord.Role, matching.Role)


class TestMember():
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


@pytest.mark.parametrize("matchees, per_group", [
    # Simplest test possible
    ([TestMember(1)], 1),

    # More requested than we have
    ([TestMember(1)], 2),

    # A selection of hyper-simple checks to validate core functionality
    ([TestMember(1)] * 100, 3),
    ([TestMember(1)] * 12, 5),
    ([TestMember(1)] * 11, 2),
    ([TestMember(1)] * 356, 8),
])
def test_matchees_to_groups_no_history(matchees, per_group):
    """Test simple group matching works"""
    hist = history.History()
    core_validate_members_to_groups(matchees, hist, per_group)


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
                    [TestMember(1), TestMember(2)],
                    [TestMember(3), TestMember(4)],
                ]
            }
        ],
        [
            TestMember(1),
            TestMember(2),
            TestMember(3),
            TestMember(4),
        ],
        2,
        [
            lambda groups: not items_found_in_lists(
                groups, [TestMember(1), TestMember(2)]),
            lambda groups: not items_found_in_lists(
                groups, [TestMember(3), TestMember(4)])
        ]
    ),
    # Feed the system an "impossible" test
    # The function should fall back to ignoring history and still give us something
    (
        [
            {
                "ts": datetime.now() - timedelta(days=1),
                "groups": [
                    [TestMember(1), TestMember(2), TestMember(3)],
                    [TestMember(4), TestMember(5), TestMember(6)],
                ]
            }
        ],
        [
            TestMember(1),
            TestMember(2),
            TestMember(3),
            TestMember(4),
            TestMember(5),
            TestMember(6),
        ],
        3,
        [
            # Nothing specific to validate
        ]
    ),
    
])
def test_matchees_to_groups_with_history(history_data, matchees, per_group, checks):
    """Test simple group matching works"""
    hist = history.History()

    # Replay the history
    for d in history_data:
        hist.log_groups_to_history(d["groups"], d["ts"])

    groups = core_validate_members_to_groups(matchees, hist, per_group)

    # Run the custom validate functions
    for check in checks:
        assert check(groups)


def core_validate_members_to_groups(matchees: list[TestMember], hist: history.History, per_group: int):
    # Convert members to groups
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
