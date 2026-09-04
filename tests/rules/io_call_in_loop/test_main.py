"""io_call_in_loop: a call that leaves the process, made once per element."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "load_rows": 2,             # `execute` and `fetchall`, two distinct calls
    "save_each": 1,             # ambiguous name on an unambiguous receiver
    "fetch_all": 1,             # the same inside a comprehension
    "fetch_one_at_a_time": 1,   # awaited in place, so still one round trip each
    "scrape": 1,                # `urlopen` imported directly
    "poll_each": 1,             # a timeout is not concurrency
}


def test_io_call_in_loop():
    check("io_call_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_io_call_in_loop()
    print("ok")
