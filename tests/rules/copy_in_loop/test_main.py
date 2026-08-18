"""copy_in_loop: a shared container duplicated once per iteration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "merge_defaults": 1,  # `dict(defaults)` per row
    "snapshot_each": 1,   # `deepcopy` inside a comprehension
    "slice_per_row": 1,   # `[:]` is a copy with different punctuation
}


def test_copy_in_loop():
    check("copy_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_copy_in_loop()
    print("ok")
