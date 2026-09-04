"""redundant_bool_branch: a branch returning the truth value it just computed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "is_configured": 1,    # truthiness, so the advice must wrap in `bool()`
    "validate_token": 1,   # the guard-clause spelling, with no `else`
    "above": 1,     # True/False for a comparison
    "missing": 1,   # the inverted form
    "is_ready": 1,  # an attribute test, same shape
}


def test_redundant_bool_branch():
    check("redundant_bool_branch", CASES, EXPECTED)


if __name__ == "__main__":
    test_redundant_bool_branch()
    print("ok")
