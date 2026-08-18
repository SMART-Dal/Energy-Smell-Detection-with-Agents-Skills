"""trivial_delegation: a body that does nothing but forward its own arguments."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "Store.fetch": 1,  # same argument, nothing added
    "Store.count": 1,  # a parameterless forward is still a forward
    "parse": 1,        # the module-level shape
}


def test_trivial_delegation():
    check("trivial_delegation", CASES, EXPECTED)


if __name__ == "__main__":
    test_trivial_delegation()
    print("ok")
