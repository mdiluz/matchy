import matchy.util as util


def test_iterate_all_shifts():
    original = [1, 2, 3, 4]
    lists = [val for val in util.iterate_all_shifts(original)]
    assert lists == [
        [1, 2, 3, 4],
        [2, 3, 4, 1],
        [3, 4, 1, 2],
        [4, 1, 2, 3],
    ]
