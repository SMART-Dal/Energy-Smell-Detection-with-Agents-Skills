"""redundant_materialisation: flag `list(...)` handed to something that consumes lazily."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "total_size": 1,           # `sum(list(genexp))`
    "ranked_names": 1,         # `sorted` builds its own list anyway
    "summarise": 2,            # two conversions in one unit
    "pair_scores": 1,          # `zip`'s second argument counts too
    "make_totaller.total": 1,  # belongs to the closure, not the factory
}


def test_redundant_materialisation():
    check("redundant_materialisation", CASES, EXPECTED)


if __name__ == "__main__":
    test_redundant_materialisation()
    print("ok")
