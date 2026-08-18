"""method_ignores_self: an instance method that never touches self."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "Report.format_cell": 1,  # never reads `self`
    "Report._slug": 1,        # a private helper that ignores it
    "Base.helper": 1,         # a plain body, not an abstract stub
}


def test_method_ignores_self():
    check("method_ignores_self", CASES, EXPECTED)


if __name__ == "__main__":
    test_method_ignores_self()
    print("ok")
