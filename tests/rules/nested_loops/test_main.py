"""nested_loops: repetition nested two deep or more, counting comprehensions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "pair_totals": 1,        # two statement loops
    "cross_products": 1,     # the same nest written as comprehensions
    "drain_pending": 1,      # a `while` inside a `for`
    "triple_scan": 1,        # three levels, reported once at the innermost
    "two_inner_loops": 2,    # two innermost nests under one outer
    "make_counter.count": 1, # the closure owns its nest, the factory does not
}


def test_nested_loops():
    check("nested_loops", CASES, EXPECTED)


if __name__ == "__main__":
    test_nested_loops()
    print("ok")
