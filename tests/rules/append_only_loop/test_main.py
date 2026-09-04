"""append_only_loop: a loop body that is nothing but an append."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "parse_all": 1,             # bare append
    "collect_names": 1,         # appending through an attribute
    "keep_valid": 1,            # an `if` around it is a comprehension filter
    "build_in_closure.run": 1,  # attributed to the closure that owns the loop
    "keep_valid_and_scored": 1, # nested `if`s are still one comprehension
}


def test_append_only_loop():
    check("append_only_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_append_only_loop()
    print("ok")
