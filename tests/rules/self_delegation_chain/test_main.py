"""self_delegation_chain: a method whose whole body calls another method of the same object."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "User.get_name": 1,  # one call, nothing added
    "User.display": 1,   # an argument passed through is still a pass-through
    "User.described": 1, # a docstring is not a statement
}


def test_self_delegation_chain():
    check("self_delegation_chain", CASES, EXPECTED)


if __name__ == "__main__":
    test_self_delegation_chain()
    print("ok")
