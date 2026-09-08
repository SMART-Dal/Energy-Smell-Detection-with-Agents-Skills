"""A meter that reports wall-clock time and a synthetic energy figure.

Used by tests and by `--meter null` on machines with no energy sensors, so the
rest of the pipeline can be exercised end to end without hardware.  Its numbers
are deterministic given the runtime, and it never claims to be `available()` for
real measurement decisions.
"""

from __future__ import annotations

import time
from typing import Callable

from ..models import Sample

# Stand-in for average package power, in watts. Chosen to be plausible so that
# reports produced with this meter look sane; it is not a measurement.
ASSUMED_POWER_W = 50.0


class NullMeter:
    """Times the callable and multiplies by a fixed assumed power draw."""

    name = "null"

    def available(self) -> bool:
        return False

    def sample(self, fn: Callable[[], object]) -> Sample:
        start = time.perf_counter()
        fn()
        duration = time.perf_counter() - start
        return Sample(
            energy_j=duration * ASSUMED_POWER_W,
            duration_s=duration,
            power_w=ASSUMED_POWER_W,
        )

    def missing_domains(self) -> tuple[str, ...]:
        """Nothing is measured, so nothing is missing in the reportable sense."""
        return ()
