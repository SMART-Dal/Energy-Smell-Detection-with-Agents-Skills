"""dead_initialization: a value assigned and overwritten before anything reads it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "load": 1,       # `[]` replaced a line later
    "summarise": 1,  # a whole comprehension discarded
}


def test_dead_initialization():
    check("dead_initialization", CASES, EXPECTED)


if __name__ == "__main__":
    test_dead_initialization()
    print("ok")
