"""
    Test functions for the matching module
"""
import discord
import pytest
import random
import matching
import state
from datetime import datetime, timedelta


def test_protocols():
    """Verify the protocols we're using match the discord ones"""
    assert isinstance(discord.Member, matching.Member)
    assert isinstance(discord.Guild, matching.Guild)
    assert isinstance(discord.Role, matching.Role)
    assert isinstance(Member, matching.Member)
    # assert isinstance(Role, matching.Role)


class Role():
    def __init__(self, id: int):
        self._id = id

    @property
    def id(self) -> int:
        return self._id


class Member():
    def __init__(self, id: int, roles: list[Role] = []):
        self._id = id
        self._roles = roles

    @property
    def mention(self) -> str:
        return f"<@{self._id}>"

    @property
    def roles(self) -> list[Role]:
        return self._roles

    @property
    def id(self) -> int:
        return self._id


def inner_validate_members_to_groups(matchees: list[Member], tmp_state: state.State, per_group: int):
    """Inner function to validate the main output of the groups function"""
    groups = matching.members_to_groups(matchees, tmp_state, per_group)

    # We should always have one group
    assert len(groups)

    # Log the groups to history
    # This will validate the internals
    tmp_state.log_groups(groups)

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
], ids=['single', "larger_groups", "100_members", "5_group", "pairs", "356_big_groups"])
def test_members_to_groups_no_history(matchees, per_group):
    """Test simple group matching works"""
    tmp_state = state.State()
    inner_validate_members_to_groups(matchees, tmp_state, per_group)


def items_found_in_lists(list_of_lists, items):
    """validates if any sets of items are found in individual lists"""
    for sublist in list_of_lists:
        if all(item in sublist for item in items):
            return True
    return False


@pytest.mark.parametrize("history_data, matchees, per_group, checks", [
    # Slightly more difficult test
    (
        # Describe a history where we previously matched up some people and ensure they don't get rematched
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
                    [
                        Member(1),
                        Member(2),
                        Member(3)
                    ],
                    [
                        Member(4),
                        Member(5),
                        Member(6)
                    ],
                ]
            }
        ],
        [
            Member(1, [Role(1), Role(2), Role(3), Role(4)]),
            Member(2, [Role(1), Role(2), Role(3), Role(4)]),
            Member(3, [Role(1), Role(2), Role(3), Role(4)]),
            Member(4, [Role(1), Role(2), Role(3), Role(4)]),
            Member(5, [Role(1), Role(2), Role(3), Role(4)]),
            Member(6, [Role(1), Role(2), Role(3), Role(4)]),
        ],
        3,
        [
            # Nothing specific to validate
        ]
    ),
    # Specific test pulled out of the stress test
    (
        [
            {
                "ts": datetime.now() - timedelta(days=4),
                "groups": [
                    [Member(i) for i in [1, 2, 3, 4, 5, 6,
                                         7, 8, 9, 10, 11, 12, 13, 14, 15]]
                ]
            },
            {
                "ts": datetime.now() - timedelta(days=5),
                "groups": [
                    [Member(i) for i in [1, 2, 3, 4, 5, 6, 7, 8]]
                ]
            }
        ],
        [Member(i) for i in [1, 2, 11, 4, 12, 3, 7, 5, 8, 10, 9, 6]],
        3,
        [
            # Nothing specific to validate
        ]
    ),
    # Silly example that failued due to bad role logic
    (
        [
            # No history
        ],
        [
            # print([(m.id, [r.id for r in m.roles]) for m in matchees]) to get the below
            Member(i, [Role(r) for r in roles]) for (i, roles) in
            [
                (4, [1, 2, 3, 4, 5, 6, 7, 8]),
                (8, [1]),
                (9, [1, 2, 3, 4, 5]),
                (6, [1, 2, 3]),
                (11, [1, 2, 3]),
                (7, [1, 2, 3, 4, 5, 6, 7]),
                (1, [1, 2, 3, 4]),
                (5, [1, 2, 3, 4, 5]),
                (12, [1, 2, 3, 4]),
                (10, [1]),
                (13, [1, 2, 3, 4, 5, 6]),
                (2, [1, 2, 3, 4, 5, 6]),
                (3, [1, 2, 3, 4, 5, 6, 7])
            ]
        ],
        2,
        [
            # Nothing else
        ]
    )
], ids=['simple_history', 'fallback', 'example_1', 'example_2'])
def test_members_to_groups_with_history(history_data, matchees, per_group, checks):
    """Test more advanced group matching works"""
    tmp_state = state.State()

    # Replay the history
    for d in history_data:
        tmp_state.log_groups(d["groups"], d["ts"])

    groups = inner_validate_members_to_groups(matchees, tmp_state, per_group)

    # Run the custom validate functions
    for check in checks:
        assert check(groups)


def test_members_to_groups_stress_test():
    """stress test firing significant random data at the code"""

    # Use a stable rand, feel free to adjust this if needed but this lets the test be stable
    rand = random.Random(123)

    # Slowly ramp up the group size
    for per_group in range(2, 6):

        # Slowly ramp a randomized shuffled list of members with randomised roles
        for num_members in range(1, 5):
            matchees = [Member(i, [Role(i) for i in range(1, rand.randint(2, num_members*2 + 1))])
                        for i in range(1, rand.randint(2, num_members*10 + 1))]
            rand.shuffle(matchees)

            for num_history in range(8):

                # Generate some super random history
                # Start some time from now to the past
                time = datetime.now() - timedelta(days=rand.randint(0, num_history*5))
                history_data = []
                for _ in range(0, num_history):
                    run = {
                        "ts": time
                    }
                    groups = []
                    for y in range(1, num_history):
                        groups.append([Member(i)
                                       for i in range(1, max(num_members, rand.randint(2, num_members*10 + 1)))])
                    run["groups"] = groups
                    history_data.append(run)

                    # Step some time backwards in time
                    time -= timedelta(days=rand.randint(1, num_history))

                # No guarantees on history data order so make it a little harder for matchy
                rand.shuffle(history_data)

                # Replay the history
                tmp_state = state.State()
                for d in history_data:
                    tmp_state.log_groups(d["groups"], d["ts"])

                inner_validate_members_to_groups(
                    matchees, tmp_state, per_group)


def test_auth_scopes():
    tmp_state = state.State()

    id = "1"
    tmp_state.set_user_scope(id, state.AuthScope.OWNER)
    assert tmp_state.get_user_has_scope(id, state.AuthScope.OWNER)
    assert tmp_state.get_user_has_scope(id, state.AuthScope.MATCHER)

    id = "2"
    tmp_state.set_user_scope(id, state.AuthScope.MATCHER)
    assert not tmp_state.get_user_has_scope(id, state.AuthScope.OWNER)
    assert tmp_state.get_user_has_scope(id, state.AuthScope.MATCHER)

    tmp_state.validate()


def test_iterate_all_shifts():
    original = [1, 2, 3, 4]
    lists = [val for val in matching.iterate_all_shifts(original)]
    assert lists == [
        [1, 2, 3, 4],
        [2, 3, 4, 1],
        [3, 4, 1, 2],
        [4, 1, 2, 3],
    ]
