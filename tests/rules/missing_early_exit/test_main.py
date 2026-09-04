"""missing_early_exit: a loop that settles one name on one value and keeps going."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "contains_target": 1,         # `found = True`, nothing can unset it
    "all_records_valid": 1,       # the answer is known at the first failure
    "scan_grid": 1,               # settled in the inner loop: one report, not two
    "scan_after_inner_break": 1,  # that `break` leaves the inner loop, not this one
    "scan_with_nested_def": 1,    # that `return` belongs to the nested function
    "walk_chain": 1,              # local mutation only, so the break is still safe
}


def test_missing_early_exit():
    check("missing_early_exit", CASES, EXPECTED)


if __name__ == "__main__":
    test_missing_early_exit()
    print("ok")
