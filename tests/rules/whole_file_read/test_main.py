"""whole_file_read: a whole source loaded, then walked a line at a time."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "dispatch_all": 1,        # producer and consumer joined through a local
    "count_errors": 1,       # read then splitlines
    "all_lines": 1,          # readlines consumed by a comprehension
    "each_record": 1,        # readlines consumed by a statement loop
    "split_on_newline": 1,   # `.split("\n")` is the same walk
}


def test_whole_file_read():
    check("whole_file_read", CASES, EXPECTED)


if __name__ == "__main__":
    test_whole_file_read()
    print("ok")
