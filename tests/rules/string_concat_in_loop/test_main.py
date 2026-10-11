"""string_concat_in_loop: flag string accumulation a second reference makes quadratic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "Report.render": 1,             # attribute target, callee returns text
    "Report.rebuild": 1,            # `s = s + x` form
    "grow_plain_local": 1,          # reported: the shape is there, though already linear
    "grow_local_and_read_it": 1,    # the read aliases it
    "group_by_key": 1,              # subscript target
    "render_grid": 1,               # nested loops, one statement, one report
    "build_bytes": 1,               # bytes concatenate the same way
    "build_row": 1,                 # `a = a + b + c`, three parts deep
    "grow_with_an_fstring": 1,      # f-strings never resize in place
    "column_label": 1,              # a prepend copies every time, even a local
}


def test_string_concat_in_loop():
    check("string_concat_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_string_concat_in_loop()
    print("ok")
