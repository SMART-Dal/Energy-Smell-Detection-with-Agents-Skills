"""eager_comprehension: a list comprehension handed to a consumer that streams."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "align_data": 1,               # a comprehension in `zip`'s second argument
    "outer_pipeline.aggregate": 1,  # reported once, against the nested def
    "total_doubled": 1,  # `sum` walks it once
    "any_failed": 1,     # `any` also stops before reading it all
}


def test_eager_comprehension():
    check("eager_comprehension", CASES, EXPECTED)


if __name__ == "__main__":
    test_eager_comprehension()
    print("ok")
