"""discarded_pure_result: a pure call whose result nothing receives."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "rank": 1,     # `sorted` builds a list nobody takes
    "measure": 1,  # `len` computed and dropped
}


def test_discarded_pure_result():
    check("discarded_pure_result", CASES, EXPECTED)


if __name__ == "__main__":
    test_discarded_pure_result()
    print("ok")
