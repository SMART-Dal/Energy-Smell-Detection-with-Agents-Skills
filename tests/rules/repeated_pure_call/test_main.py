"""repeated_pure_call: the same call three times in one scope."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "summarise": 1,   # `parse_manifest(path)` three times, nothing changing
    "audit_data": 1,  # three independent `if`s all run; not alternatives
}


def test_repeated_pure_call():
    check("repeated_pure_call", CASES, EXPECTED)


if __name__ == "__main__":
    test_repeated_pure_call()
    print("ok")
