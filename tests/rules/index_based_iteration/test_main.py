"""index_based_iteration: `range(len(xs))` where the index only reads back into a sequence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "doubled": 1,          # the index exists only to subscript
    "absolute_gaps": 1,    # one index over two sequences; `zip` is the repair
    "matrix_diagonal": 1,  # the same shape inside a comprehension
}


def test_index_based_iteration():
    check("index_based_iteration", CASES, EXPECTED)


if __name__ == "__main__":
    test_index_based_iteration()
    print("ok")
