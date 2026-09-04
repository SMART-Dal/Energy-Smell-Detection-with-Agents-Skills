"""mutable_default_argument: flag a mutable object created once at definition time."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "batch_process": 2,       # two comprehension defaults, both shared
    "collect_samples": 1,           # list literal, appended to
    "Registry.register": 2,         # two defaults on one signature, two findings
    "tally_words": 1,               # keyword-only default
    "build_index": 1,               # `collections.defaultdict(list)`, qualified
    "memoised_fib": 1,              # deliberate memo, still a shared mutable
    "make_collector.collect": 1,    # the inner signature, charged to the inner unit
}


def test_mutable_default_argument():
    check("mutable_default_argument", CASES, EXPECTED)


if __name__ == "__main__":
    test_mutable_default_argument()
    print("ok")
