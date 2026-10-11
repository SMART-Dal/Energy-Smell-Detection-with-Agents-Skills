"""repeated_subscript_in_loop: flag the same lookup by key repeated within one pass."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "tally": 1,       # `d[k]` three times in one pass
    "describe": 1,    # the same in a comprehension
    "columns": 1,     # `rows[i]`, once, not once per field
    "by_id": 1,       # key bound before the first read
}


def test_repeated_subscript_in_loop():
    check("repeated_subscript_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_repeated_subscript_in_loop()
    print("ok")
