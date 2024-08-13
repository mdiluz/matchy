"""
    Test functions for the matching module
"""
import discord
import pytest
import random
import matching
import state
import copy
import itertools
from datetime import datetime, timedelta


def test_protocols():
    """Verify the protocols we're using match the discord ones"""
    assert isinstance(discord.Member, matching.Member)
    assert isinstance(discord.Guild, matching.Guild)
    assert isinstance(discord.Role, matching.Role)
    assert isinstance(Member, matching.Member)
    assert isinstance(Role, matching.Role)


class Role():
    def __init__(self, id: int):
        self._id = id

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        pass


class Member():
    def __init__(self, id: int, roles: list[Role] = []):
        self._id = id
        self._roles = roles

    @property
    def mention(self) -> str:
        return f"<@{self._id}>"

    @property
    def display_name(self) -> str:
        return f"{self._id}"

    @property
    def roles(self) -> list[Role]:
        return self._roles

    @roles.setter
    def roles(self, roles: list[Role]):
        self._roles = roles

    @property
    def id(self) -> int:
        return self._id


def members_to_groups_validate(matchees: list[Member], tmp_state: state.State, per_group: int):
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
    members_to_groups_validate(matchees, tmp_state, per_group)


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
    ),
    # Another weird one pulled out of the stress test
    (
        [
            # print([(str(h["ts"]), [[f"Member({gm.id})" for gm in g] for g in h["groups"]]) for h in history_data])
            {"ts": datetime.strptime(ts, r"%Y-%m-%d %H:%M:%S.%f"), "groups": [
                [Member(m) for m in group] for group in groups]}
            for (ts, groups) in
            [
                (
                    '2024-07-07 20:25:56.313993',
                    [
                        [1, 2, 3, 4, 5],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                        [1],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
                        [1, 2, 3, 4, 5, 6, 7, 8]
                    ]
                ),
                (
                    '2024-07-13 20:25:56.313993',
                    [
                        [1, 2],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                            12, 13, 14, 15, 16, 17, 18],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        [1]
                    ]
                ),
                (
                    '2024-06-29 20:25:56.313993',
                    [
                        [1, 2, 3, 4, 5],
                        [1, 2, 3, 4, 5, 6, 7],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                            13, 14, 15, 16, 17, 18, 19, 20],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                            11, 12, 13, 14, 15, 16, 17],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                            12, 13, 14, 15, 16, 17, 18, 19, 20]
                    ]
                ),
                (
                    '2024-06-25 20:25:56.313993',
                    [
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                            12, 13, 14, 15, 16, 17, 18],
                        [1, 2],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                            12, 13, 14, 15, 16, 17, 18, 19],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                        [1, 2]
                    ]
                ),
                (
                    '2024-07-04 20:25:56.313993',
                    [
                        [1, 2, 3, 4, 5],
                        [1, 2, 3],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                        [1, 2, 3, 4, 5, 6, 7]
                    ]
                ),
                (
                    '2024-07-16 20:25:56.313993',
                    [
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                            13, 14, 15, 16, 17, 18, 19, 20],
                        [1, 2, 3, 4, 5, 6],
                        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                            11, 12, 13, 14, 15, 16, 17, 18]
                    ]
                )
            ]
        ],
        [
            # print([(m.id, [r.id for r in m.roles]) for m in matchees]) to get the below
            Member(i, [Role(r) for r in roles]) for (i, roles) in
            [
                (10, [1, 2, 3]),
                (4, [1, 2, 3]),
                (5, [1, 2]),
                (13, [1, 2]),
                (3, [1, 2, 3, 4]),
                (14, [1]),
                (6, [1, 2, 3, 4]),
                (11, [1]),
                (9, [1]),
                (1, [1, 2, 3]),
                (16, [1, 2]),
                (15, [1, 2]),
                (2, [1, 2, 3]),
                (7, [1, 2, 3]),
                (12, [1, 2]),
                (8, [1, 2, 3, 4])
            ]
        ],
        5,
        [
            # Nothing
        ]
    )
], ids=['simple_history', 'fallback', 'example_1', 'example_2', 'example_3'])
def test_unique_regressions(history_data, matchees, per_group, checks):
    """Test a bunch of unqiue failures that happened in the past"""
    tmp_state = state.State()

    # Replay the history
    for d in history_data:
        tmp_state.log_groups(d["groups"], d["ts"])

    groups = members_to_groups_validate(matchees, tmp_state, per_group)

    # Run the custom validate functions
    for check in checks:
        assert check(groups)


def random_chunk(li, min_chunk, max_chunk, rand):
    """
    "Borrowed" from https://stackoverflow.com/questions/21439011/best-way-to-split-a-list-into-randomly-sized-chunks
    """
    it = iter(li)
    while True:
        nxt = list(itertools.islice(it, rand.randint(min_chunk, max_chunk)))
        if nxt:
            yield nxt
        else:
            break


# Generate a large set of "interesting" tests that replay a fake history onto random people
# Increase these numbers for some extreme programming
@pytest.mark.parametrize("per_group, num_members, num_history", (
    (per_group, num_members, num_history)
    # Most of the time groups are gonna be from 2 to 5
    for per_group in range(2, 5)
    # Going lower than 8 members doesn't give the bot much of a chance
    # And it will fail to not fall back sometimes
    # That's probably OK frankly
    for num_members in range(8, 32, 5)
    # Throw up to 7 histories at the algorithmn
    for num_history in range(0, 8)))
def test_stess_random_groups(per_group, num_members, num_history):
    """Run a randomised test based on the input"""

    # Seed the random based on the inputs paird with primes
    # Ensures the test has interesting fake data, but is stable
    rand = random.Random(per_group*3 + num_members*5 + num_history*7)

    # Start with a list of all possible members
    possible_members = [Member(i) for i in range(num_members*2)]
    for member in possible_members:
        # Give each member 3 random roles from 1-7
        member.roles = [Role(i) for i in rand.sample(range(1, 8), 3)]

    # For each history item match up groups and log those
    cumulative_state = state.State()
    for i in range(num_history+1):

        # Grab the num of members and replay
        rand.shuffle(possible_members)
        members = copy.deepcopy(possible_members[:num_members])

        groups = members_to_groups_validate(
            members, cumulative_state, per_group)
        cumulative_state.log_groups(
            groups, datetime.now() - timedelta(days=num_history-i))


def test_auth_scopes():
    tmp_state = state.State()

    id = "1"
    assert not tmp_state.get_user_has_scope(id, state.AuthScope.MATCHER)

    id = "2"
    tmp_state.set_user_scope(id, state.AuthScope.MATCHER)
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
