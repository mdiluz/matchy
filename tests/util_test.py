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


def test_get_nested_dict_value():
    d = {
        "x": {
            "y": {
                "z": {
                    "val": 42
                }
            }
        }
    }
    assert 42 == util.get_nested_value(d, "x", "y", "z", "val")
    assert 16 == util.get_nested_value(d, "x", "y", "z", "vol", default=16)


def test_set_nested_dict_value():
    d = {
        "x": {
            "y": {
                "z": {
                    "val": 42
                }
            }
        }
    }
    util.set_nested_value(d, "x", "y", "z", "val", value=52)
    assert 52 == util.get_nested_value(d, "x", "y", "z", "val")


def test_randomized():

    def string():
        return "foo"

    def list():
        return ["foo", "bar"]

    assert util.randomised(string)() == "foo"
    assert util.randomised(list)() in list()
