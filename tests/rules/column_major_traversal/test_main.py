"""column_major_traversal: walking a row-major array down its columns."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "column_sums": 1,    # `matrix[:, j]` inside a loop
    "column_maxima": 1,  # the same access in a comprehension
    "through_values": 1,  # `.values` is an ndarray again, so the layout matters
}


def test_column_major_traversal():
    check("column_major_traversal", CASES, EXPECTED)


if __name__ == "__main__":
    test_column_major_traversal()
    print("ok")
