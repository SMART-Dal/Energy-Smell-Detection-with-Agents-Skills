"""expensive_operand_first: flag a call placed ahead of a cheaper, independent test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "visible_rows": 1,                  # call before an attribute read
    "should_retry": 1,                  # expensive operand is a sub-expression
    "needs_rebuild": 1,                 # `or` chain, cheap flag second
    "SessionCache.should_evict": 1,     # reported: the call may be a side effect
    "worth_processing": 1,              # `len(data) > 0` is a cheap guard
}


def test_expensive_operand_first():
    check("expensive_operand_first", CASES, EXPECTED)


if __name__ == "__main__":
    test_expensive_operand_first()
    print("ok")
