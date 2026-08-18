"""expensive_comparison: a comparison that builds an object to answer yes or no."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "same_members": 1,  # two sorts and two lists
    "same_text": 1,     # two conversions, per element
    "same_set": 1,      # two containers for one comparison
}


def test_expensive_comparison():
    check("expensive_comparison", CASES, EXPECTED)


if __name__ == "__main__":
    test_expensive_comparison()
    print("ok")
