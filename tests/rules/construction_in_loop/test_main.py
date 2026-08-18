"""construction_in_loop: objects built fresh on every iteration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "group_rows": 1,       # a dict literal per row
    "select_allowed": 1,   # a set comprehension depending only on `limit`
    "sort_each_group": 1,  # a lambda built per element of a comprehension
    "tally_by_kind": 1,    # `dict()` is a constructor call
}


def test_construction_in_loop():
    check("construction_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_construction_in_loop()
    print("ok")
