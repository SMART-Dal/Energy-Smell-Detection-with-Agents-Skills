"""independent_exclusive_ifs: flag runs of separate `if`s an elif chain would cut short."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "route_event": 1,               # three unchained arms on one local
    "ReportStyle.decorate": 1,      # attribute subject
    "apply_directives": 2,          # two runs in one body
    "load_config": 1,               # run inside an except handler
}


def test_independent_exclusive_ifs():
    check("independent_exclusive_ifs", CASES, EXPECTED)


if __name__ == "__main__":
    test_independent_exclusive_ifs()
    print("ok")
