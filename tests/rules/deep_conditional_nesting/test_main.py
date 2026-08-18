"""deep_conditional_nesting: flag `if` nests deep enough that guard clauses would flatten them."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "dispatch_request": 1,          # five levels, one test repeated
    "ImportPlan.resolve": 1,        # five levels reached through loops
    "parse_header": 1,              # `with` between the levels still counts
    "build_validator.check": 1,     # the nest is the closure's, and only the closure's
}


def test_deep_conditional_nesting():
    check("deep_conditional_nesting", CASES, EXPECTED)


if __name__ == "__main__":
    test_deep_conditional_nesting()
    print("ok")
