"""loop_invariant_expression: flag per-iteration work whose value never changes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {

    "filter_rows": 1,        # call wrapping a subscript: the outer one only
    "take_while_small": 1,   # `len()` in a while condition really does re-run
    "cross_check": 1,        # nested loops, one expression, one report
    "score_all": 1,          # constant subscript into a module-level table
    "normalise": 1,          # `sum()` per element: a quadratic comprehension
    "row_products": 1,       # `a[i]` does not vary with the inner generator
}


def test_loop_invariant_expression():
    check("loop_invariant_expression", CASES, EXPECTED)


if __name__ == "__main__":
    test_loop_invariant_expression()
    print("ok")
