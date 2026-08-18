"""float_literal_on_int_data: flag a whole-number float literal in repeated arithmetic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "multiply_elements": 1,    # `[n * 3.0 ...]`, the measured +39% case
    "scale_row_widths": 1,     # same multiply inside a `for` body
    "stack_bar_offsets": 1,    # augmented assignment carries the literal
    "countdown_ticks": 1,      # subtraction inside a `while`
}


def test_float_literal_on_int_data():
    check("float_literal_on_int_data", CASES, EXPECTED)


if __name__ == "__main__":
    test_float_literal_on_int_data()
    print("ok")
