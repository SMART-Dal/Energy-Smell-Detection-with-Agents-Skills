"""regex_in_loop: regex work repeated per element with an invariant pattern."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "extract_ids": 1,        # `re.search` per line
    "strip_tags": 1,         # the same inside a comprehension
    "compile_each_time": 1,  # `re.compile` on a fixed pattern in the body
    "scan_with_direct_import": 1,   # `from re import search`
    "scan_with_keyword_args": 1,    # `pattern=` instead of positional
    "scan_with_finditer": 1,        # `finditer` was not in the list
    "scan_with_renamed_module": 1,  # `import re as regex`
}


def test_regex_in_loop():
    check("regex_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_regex_in_loop()
    print("ok")
