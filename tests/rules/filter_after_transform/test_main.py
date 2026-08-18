"""filter_after_transform: flag a bulk transform whose result is filtered afterwards."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "summarise_documents": 1,     # list comprehension transform, filtered next line
    "render_visible_cards": 1,    # `list(map(f, xs))` then a filtering comprehension
    "weigh_records": 1,           # generator transform: still one call per record
    "positive_scores": 1,         # element expression recomputed in its own test
}


def test_filter_after_transform():
    check("filter_after_transform", CASES, EXPECTED)


if __name__ == "__main__":
    test_filter_after_transform()
    print("ok")
