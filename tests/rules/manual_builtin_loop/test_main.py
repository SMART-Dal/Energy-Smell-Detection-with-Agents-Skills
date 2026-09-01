"""manual_builtin_loop: a loop hand-rolling max, min or sum."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {

    "total_even": 1,      # `if` around `+= value` is a comprehension filter
    "largest": 1,         # a running maximum
    "total": 1,           # a running total
    "smallest_score": 1,  # a running minimum behind a `None` guard
    "best_record": 1,     # tracks the element; `max(key=...)` is the repair
}


def test_manual_builtin_loop():
    check("manual_builtin_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_manual_builtin_loop()
    print("ok")
