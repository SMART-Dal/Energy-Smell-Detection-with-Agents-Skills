"""sort_then_slice: a full sort whose result is immediately truncated."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "top_k": 1,     # sorts everything to keep k
    "cheapest": 1,  # `sorted(...)[0]` is `min`
    "newest": 1,    # `[-1]` is `max`; it parses as a UnaryOp, not a Constant
    "sum_top": 1,   # nested inside another call
}


def test_sort_then_slice():
    check("sort_then_slice", CASES, EXPECTED)


if __name__ == "__main__":
    test_sort_then_slice()
    print("ok")
