"""global_lookup_in_loop: flag names re-resolved through the module namespace per iteration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "count_exhausted": 1,     # MAX_RETRIES read 3x, log_warning 1x stays under
    "render_rows": 1,         # builtin `str` read 3x per row
    "score_matrix": 1,        # nested loops, one name: one report, not one per level
    "summarise_batch": 2,     # two names over the threshold, both inside the cap
    "classify_tokens": 2,     # three names over it, capped at the worst two
    "scale_readings": 1,      # a comprehension repeats as hard as a loop
    "total_readings": 1,      # and so does a generator expression
}


def test_global_lookup_in_loop():
    check("global_lookup_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_global_lookup_in_loop()
    print("ok")
