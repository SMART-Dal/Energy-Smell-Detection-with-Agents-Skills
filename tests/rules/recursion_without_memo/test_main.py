"""recursion_without_memo: self-recursion that re-solves overlapping subproblems."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "fib": 1,          # two self-calls per level
    "count_paths": 1,  # the same tree written over two lines
    "factorial": 1,    # linear recursion; same analyzer, `linear_recursion` kind
}


def test_recursion_without_memo():
    check("recursion_without_memo", CASES, EXPECTED)


if __name__ == "__main__":
    test_recursion_without_memo()
    print("ok")
