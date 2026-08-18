"""try_except_in_loop: exception handling on the per-iteration path."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "lookup_all": 1,   # a raise per missing key
    "parse_ports": 1,  # the same inside a `while`
    "load_each": 1,    # nested loops, one `try`, one report
}


def test_try_except_in_loop():
    check("try_except_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_try_except_in_loop()
    print("ok")
