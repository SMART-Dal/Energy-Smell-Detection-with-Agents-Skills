"""Direct Intel RAPL meter, reading the powercap sysfs interface.

This is the fallback for machines where CodeGreen is unavailable, and it doubles
as a cross-check -- the two meters should agree closely on the same workload,
and a host where they do not is a host worth investigating before trusting a
batch from it.

RAPL counters are free-running microjoule registers that wrap around, so every
read is a delta against the previous one with explicit wrap handling.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from ..models import Sample
from .base import DEFAULT_DOMAINS

POWERCAP_ROOT = Path("/sys/class/powercap")


class _Counter:
    """One RAPL domain's energy register."""

    def __init__(self, directory: Path):
        self.name = (directory / "name").read_text().strip()
        self._energy_file = directory / "energy_uj"
        self._wrap_at = int((directory / "max_energy_range_uj").read_text())

    def read_uj(self) -> int:
        return int(self._energy_file.read_text())

    def delta_uj(self, before: int, after: int) -> int:
        """Energy consumed between two reads, accounting for counter wrap."""
        delta = after - before
        return delta if delta >= 0 else delta + self._wrap_at


def _discover(domains: tuple[str, ...]) -> list[_Counter]:
    """Find readable RAPL counters whose name matches a requested domain.

    Domain directories are named like "package-0" and "dram", so we match by
    prefix.  Unreadable counters (permissions) are skipped rather than fatal.
    """
    found = []
    for directory in sorted(POWERCAP_ROOT.glob("intel-rapl:*")):
        try:
            counter = _Counter(directory)
            counter.read_uj()
        except (OSError, ValueError):
            continue
        if any(counter.name.startswith(d) for d in domains):
            found.append(counter)
    return found


class RaplMeter:
    """Measures energy by differencing RAPL registers around a call."""

    name = "rapl"

    def __init__(self, domains: tuple[str, ...] = DEFAULT_DOMAINS):
        self._domains = domains
        self._counters = _discover(domains) if POWERCAP_ROOT.exists() else []

    def available(self) -> bool:
        return bool(self._counters)

    def sample(self, fn: Callable[[], object]) -> Sample:
        if not self._counters:
            raise RuntimeError(
                "no readable RAPL counters; run as root or use --meter codegreen"
            )
        before = [c.read_uj() for c in self._counters]
        start = time.perf_counter()
        fn()
        duration = time.perf_counter() - start
        after = [c.read_uj() for c in self._counters]

        microjoules = sum(
            counter.delta_uj(b, a)
            for counter, b, a in zip(self._counters, before, after)
        )
        return Sample(energy_j=microjoules / 1e6, duration_s=duration)
