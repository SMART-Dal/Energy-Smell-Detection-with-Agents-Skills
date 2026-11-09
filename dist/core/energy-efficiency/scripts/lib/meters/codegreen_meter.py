"""CodeGreen-backed meter -- the default on supported hardware.

CodeGreen (Rajput & Sharma, 2026) polls hardware sensors from a native backend
and reports per-domain energy, which is more portable than reading RAPL sysfs
directly (it also covers macOS and Windows).

`Session.stop()` returns the whole report as a dict -- `meta`, `tasks` and
`totals` -- so nothing is written to disk and nothing is read back.  The
numbers are taken from `totals`, which is CodeGreen's aggregate for the run.

The session has to contain a task: one that starts and stops with nothing
inside it reports no energy at all.  With a single task `totals` and that task
agree to the last digit, so which one is read makes no difference to the value.

Every figure here is CodeGreen's own.  `totals.energy_j` is not re-derived from
the per-domain breakdown, because that breakdown is not disjoint -- on Intel
the package domain already contains `core`/`pp0` -- and summing it
double-counts.  Power is read from the task's `avg_power_w` rather than divided
out of energy and duration, which is the same number to fifteen digits but is
CodeGreen's arithmetic rather than ours.  Nothing is subtracted from any of it:
no idle baseline, no attribution to this process.  See `measure.py` for why.
"""

from __future__ import annotations

from typing import Callable

from ..models import Sample
from .base import DEFAULT_DOMAINS


class CodeGreenMeter:
    """Measures energy via a CodeGreen session with a single task."""

    name = "codegreen"

    def __init__(self, domains: tuple[str, ...] = DEFAULT_DOMAINS):
        self._domains = domains
        try:
            import codegreen

            self._codegreen = codegreen
        except ImportError:
            self._codegreen = None

    def available(self) -> bool:
        return self._codegreen is not None

    def sample(self, fn: Callable[[], object]) -> Sample:
        if self._codegreen is None:
            raise RuntimeError("codegreen is not installed; pip install codegreen")

        session = self._codegreen.Session(
            "energy-verify", save_to_file=False, warn_on_concurrent=False
        )
        session.start()
        session.start_task("workload")
        try:
            fn()
        finally:
            session.stop_task()
            report = session.stop()

        totals = report.get("totals") or {}
        tasks = report.get("tasks") or [{}]
        meta = report.get("meta") or {}
        return Sample(
            energy_j=totals.get("energy_j", 0.0),
            # The summed task time, which is the window the energy was
            # accumulated over. `wall_duration_s` also counts the gap outside
            # the task, and would not divide into the energy correctly.
            duration_s=totals.get("duration_s", 0.0),
            power_w=tasks[-1].get("avg_power_w", 0.0),
            domains_j=dict(totals.get("domains") or {}),
            domains_power_w=dict(totals.get("domains_power_w") or {}),
            quality=meta.get("measurement_quality"),
        )

    def visible_domains(self) -> tuple[str, ...]:
        """Domain names this host actually reports, measured not assumed.

        A RAPL sub-domain the current user cannot read is simply absent from
        CodeGreen's output, so the only honest way to know what a reading
        covers is to take one.
        """
        return tuple(sorted(self.sample(lambda: None).domains_j or {}))

    def missing_domains(self) -> tuple[str, ...]:
        """Requested domains with no counter behind them on this host."""
        seen = self.visible_domains()
        return tuple(
            requested
            for requested in self._domains
            if not any(name.startswith(requested) for name in seen)
        )
