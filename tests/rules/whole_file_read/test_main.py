"""whole_file_read: an unbounded read that loads a whole source."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "count_errors": 1,   # read then split
    "all_lines": 1,      # `readlines` is the same load
    "response_body": 1,  # any handle-like receiver counts
}


def test_whole_file_read():
    check("whole_file_read", CASES, EXPECTED)


if __name__ == "__main__":
    test_whole_file_read()
    print("ok")
