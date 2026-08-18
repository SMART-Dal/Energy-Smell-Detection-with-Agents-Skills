"""single_use_temporary: a local bound only to be returned on the next line."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "render": 1,        # the canonical shape
    "tenure_days": 1,   # the naming is deliberate; the rule stays advisory
    "two_names": 1,     # `second` is bound and returned; `first` is a different smell
}


def test_single_use_temporary():
    check("single_use_temporary", CASES, EXPECTED)


if __name__ == "__main__":
    test_single_use_temporary()
    print("ok")
