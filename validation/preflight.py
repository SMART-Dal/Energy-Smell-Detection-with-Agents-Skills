#!/usr/bin/env python3
"""Check the measurement rig before trusting anything it says.

    python validation/preflight.py

Three questions, in order, and the run stops at the first `no`:

    1. Is the host quiet?      identical code against itself must read ~0%
    2. Does it see a saving?   a set lookup must beat a linear list scan
    3. Does it see a loss?     the same comparison, reversed, must read negative

Question 1 alone is not enough. A meter that always returns the same number
would pass it perfectly, and so would one that is not connected to anything.
Questions 2 and 3 are there because a rig that cannot tell a 100x algorithmic
difference from noise, or that reports a saving whichever way round the
variants are, is broken in a way the canary cannot detect.

Run this before a validation batch. Nothing measured on a host that fails it is
worth recording -- a busy machine does not produce wrong numbers so much as
unresolvable ones, and those get written down as "the repair saves nothing".
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from verify import USABLE_FLOOR_PCT, verify  # noqa: E402

PREFLIGHT_DIR = Path(__file__).resolve().parent / "preflight"

MIN_EXPECTED_SAVING_PCT = 40.0
"""How much the known-good repair must show before the rig is believed.

Set far below the effect's real size -- a set lookup beats a 5000-element scan
by well over 90% -- so this fails only when the rig is genuinely blind, not
when the host is merely a little busy.
"""


def main() -> int:
    print("preflight: checking the measurement rig\n")

    print("1. noise floor  (identical code against itself, expect ~0%)")
    floor = verify(PREFLIGHT_DIR / "null.py", canary=False, log=_quiet)
    reading = abs(_saving(floor))
    _report_coverage(floor)
    print(f"   canary reads {reading:+.2f}%   floor for a usable host is "
          f"{USABLE_FLOOR_PCT:.1f}%")
    if reading > USABLE_FLOOR_PCT:
        print(f"\n   FAIL -- this host cannot resolve anything smaller than "
              f"{reading:.1f}%.\n   Stop other work on the machine and re-run. "
              f"Measuring now produces\n   `refuted` verdicts that are really "
              f"`we could not tell`.")
        return 1
    print("   ok\n")

    print(f"2. known saving  (set lookup vs list scan, expect > "
          f"{MIN_EXPECTED_SAVING_PCT:.0f}%)")
    good = verify(PREFLIGHT_DIR / "known_saving.py", canary=False, log=_quiet)
    print(f"   measured {_saving(good):+.1f}%   verdict {good.status}")
    if _saving(good) < MIN_EXPECTED_SAVING_PCT:
        print("\n   FAIL -- the rig cannot see an effect it should not be able "
              "to miss.\n   The meter is probably not reading this process.")
        return 1
    print("   ok\n")

    print("3. known loss  (the same pair, swapped, expect a negative number)")
    bad = verify(PREFLIGHT_DIR / "known_loss.py", canary=False, log=_quiet)
    print(f"   measured {_saving(bad):+.1f}%   verdict {bad.status}")
    if _saving(bad) > -MIN_EXPECTED_SAVING_PCT:
        print("\n   FAIL -- swapping the variants did not swap the sign.\n"
              "   The rig reports a saving whichever way round it is asked.")
        return 1
    print("   ok\n")

    print(f"preflight passed: noise floor {reading:.2f}%, "
          f"direction and magnitude both correct.")
    return 0


def _report_coverage(result) -> None:
    """Say what the readings actually covered before any of them are believed.

    A domain the current user cannot read is skipped without complaint, so a
    rig can pass all three checks below while measuring one socket and no
    memory. That is not a failure -- a narrower reading is still a valid
    paired comparison -- but it is not what the batch intends to measure, and
    finding out afterwards costs the whole batch.
    """
    coverage = result.coverage
    if not coverage:
        return
    print(f"   meter {coverage['meter']}, domains "
          f"{', '.join(coverage['visible_domains']) or 'none'}")
    if coverage["missing_domains"]:
        print(f"   WARNING: no counter for "
              f"{', '.join(coverage['missing_domains'])} on this host.\n"
              f"   Fix the powercap permissions before trusting the batch.")


def _saving(result) -> float:
    deciding = result.deciding
    return deciding.energy_saved_pct if deciding else 0.0


def _quiet(*_args, **_kwargs) -> None:
    """Swallow the per-stage log; preflight prints its own summary."""


if __name__ == "__main__":
    raise SystemExit(main())
