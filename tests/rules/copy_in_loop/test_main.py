"""copy_in_loop: a shared container duplicated once per iteration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "stage_configs": 1,       # a dotted receiver is still a copy
}
# `refresh_scratch` and `slice_per_row` are deliberately absent. Both copy,
# then mutate the copy, then append it -- so every pass needs its own and
# hoisting would leave each row sharing one container. `refresh_scratch` is
# character-for-character `merge_defaults`, which was already silent because a
# constructor is not a copy spelling; reporting one and not the other gave the
# same code two answers depending on punctuation.


def test_copy_in_loop():
    check("copy_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_copy_in_loop()
    print("ok")
