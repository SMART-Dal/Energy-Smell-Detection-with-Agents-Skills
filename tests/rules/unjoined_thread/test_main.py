"""unjoined_thread: a worker started and never joined."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "spawn_worker": 1,  # started, returned, never joined
    "fan_out": 1,       # one per job, none joined
}


def test_unjoined_thread():
    check("unjoined_thread", CASES, EXPECTED)


if __name__ == "__main__":
    test_unjoined_thread()
    print("ok")
