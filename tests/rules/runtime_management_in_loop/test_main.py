"""runtime_management_in_loop: interpreter housekeeping called per element."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "process_all": 1,  # `gc.collect()` per batch
    "reindex": 1,      # the same inside a comprehension
}


def test_runtime_management_in_loop():
    check("runtime_management_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_runtime_management_in_loop()
    print("ok")
