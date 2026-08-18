"""repeated_lookup_in_loop: flag attribute chains re-resolved on every pass."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import check  # noqa: E402

CASES = Path(__file__).with_name("test_cases.py")

EXPECTED = {
    "Gauge.clamp": 1,      # one chain, however many links it has
    "render_matrix": 1,    # nested loops share one chain and one finding
    "flush_all": 1,        # bound method resolved twice a pass
    "apply_theme": 1,      # the plain two-link case
}


def test_repeated_lookup_in_loop():
    check("repeated_lookup_in_loop", CASES, EXPECTED)


if __name__ == "__main__":
    test_repeated_lookup_in_loop()
    print("ok")
