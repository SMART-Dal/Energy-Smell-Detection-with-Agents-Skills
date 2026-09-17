"""mutation_during_iteration: mutating the collection a `for` loop is walking."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "drop_inactive": 1,   # `remove` skips the next element
    "expand_queue": 1,    # `append` can extend the loop unboundedly
    "prune_pending": 1,   # the collection is an attribute
    "drain_queue": 1,     # `del queue[0]` is a mutation too
    "shuffle_while_walking": 1,  # so is reordering in place
    "insert_derived_key": 1,     # a new key raises RuntimeError mid-iteration
    "pop_while_enumerating": 1,  # `enumerate` still walks the live collection
}


def test_mutation_during_iteration():
    check("mutation_during_iteration", CASES, EXPECTED)


if __name__ == "__main__":
    test_mutation_during_iteration()
    print("ok")
