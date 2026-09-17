"""index_based_iteration: `range(len(xs))` where the index only reads back into a sequence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "doubled": 1,          # the index exists only to subscript
    "absolute_gaps": 1,    # one index over two sequences; `zip` is the repair
    "find_position": 1,    # the index is carried out of the loop; `enumerate`
    "strip_in_place": 1,   # a write-back still has a read to remove; `enumerate`
    "every_other": 1,      # a stride is a slice: `values[::2]`
    "matrix_diagonal": 1,  # the same shape inside a comprehension
    "reverse_walk": 1,     # `range(len(x) - 1, -1, -1)` is `reversed(x)`
}


def test_index_based_iteration():
    check("index_based_iteration", CASES, EXPECTED)


if __name__ == "__main__":
    test_index_based_iteration()
    print("ok")
