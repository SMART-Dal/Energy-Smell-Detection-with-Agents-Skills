"""blocking_call_in_async: a synchronous blocking call inside a coroutine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "poll_status": 2,        # `sleep` and `get` imported directly
    "poll": 1,       # `time.sleep` stalls the loop
    "fetch_all": 1,  # a synchronous HTTP client in a coroutine
}


def test_blocking_call_in_async():
    check("blocking_call_in_async", CASES, EXPECTED)


if __name__ == "__main__":
    test_blocking_call_in_async()
    print("ok")
