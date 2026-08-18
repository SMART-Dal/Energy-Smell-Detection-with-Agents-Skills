"""constant_sequence_literal: a never-mutated list of constants that a tuple would replace."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "assign_type": 1,    # rebuilt per call, only indexed
    "bucket_for": 1,     # the same inside a loop
    "rebind_later": 2,   # two literals; rebinding is not mutation
}


def test_constant_sequence_literal():
    check("constant_sequence_literal", CASES, EXPECTED)


if __name__ == "__main__":
    test_constant_sequence_literal()
    print("ok")
