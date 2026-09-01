"""membership_test_on_sequence: flag a linear scan where a hash probe would do."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {

    "count_unique": 1,    # accumulator seeded `[]`, grown to N by `.append`
    "filter_allowed": 1,  # parameter annotated `list`
    "dedupe": 1,          # comprehension rebuilt per row, then scanned
    "grant_all": 1,       # literal plus a call: sequence-valued, size unknown
    "match_pairs": 1,     # nested loops, one comparison, one finding
    "missing_ids": 1,     # `not in` against a materialised list
    "reject_agents": 1,   # module constant, scanned inside a comprehension
}


def test_membership_test_on_sequence():
    check("membership_test_on_sequence", CASES, EXPECTED)


if __name__ == "__main__":
    test_membership_test_on_sequence()
    print("ok")
