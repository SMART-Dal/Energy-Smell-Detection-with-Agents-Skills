"""lock_in_loop: a lock acquired once per iteration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "tally": 1,  # `with self._lock` inside the loop
    "drain": 1,  # the explicit acquire; the release is not a second finding
}


def test_lock_in_loop():
    check("lock_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_lock_in_loop()
    print("ok")
