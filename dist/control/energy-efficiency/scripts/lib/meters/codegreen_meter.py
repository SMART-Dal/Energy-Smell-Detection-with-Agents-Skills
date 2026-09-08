"""CodeGreen-backed meter -- the default on supported hardware.

CodeGreen (Rajput & Sharma, 2026) polls hardware sensors from a native backend
and reports per-domain energy, which is more portable than reading RAPL sysfs
directly (it also covers macOS and Windows).

The reported number is CodeGreen's own `TaskResult.energy_j`, taken verbatim.
We do not re-derive it from the per-domain breakdown, because that breakdown is
deliberately *not* disjoint: on Intel the package domain already contains
`core`/`pp0` and `pp1`, while `dram` is a physically separate counter.  Summing
the dict double-counts; `energy_j` is the value CodeGreen already aggregates
correctly over top-level domains only.  `domains` is still carried alongside,
as a record of what the host actually exposed rather than as an input to the
arithmetic.

Nothing is subtracted from the reading -- no idle baseline, no attribution to
this process.  See `measure.py` for why.
"""

from __future__ import annotations

from typing import Callable

from ..models import Sample
from .base import DEFAULT_DOMAINS


class CodeGreenMeter:
    """Measures energy via a CodeGreen session with a single task."""

    name = "codegreen"

    def __init__(
        self,
        domains: tuple[str, ...] = DEFAULT_DOMAINS,
        *,
        record_time_series: bool = False,
    ):
        self._domains = domains
        # Time series buys per-sample power and CodeGreen's noise/quality
        # summary, but its drain thread competes with the workload and widens
        # run-to-run spread (~1% CV to ~5% on CodeGreen's own benchmarks).
        # That is the very spread our confidence intervals are built from, so
        # it stays off for measurement runs and is opt-in for diagnosis.
        self._record_time_series = record_time_series
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
            "energy-verify",
            save_to_file=False,
            warn_on_concurrent=False,
            record_time_series=self._record_time_series,
        )
        session.start()
        session.start_task("workload")
        try:
            fn()
        finally:
            session.stop_task()
            session.stop()

        result = session.tasks[-1]
        noise = getattr(result, "noise", None) or {}
        return Sample(
            energy_j=result.energy_j,
            duration_s=result.duration_s,
            power_w=result.avg_power_w,
            domains_j=dict(getattr(result, "domains", None) or {}),
            quality=noise.get("quality"),
            power_cv_pct=noise.get("power_cv_percent"),
        )

    def visible_domains(self) -> tuple[str, ...]:
        """Domain names this host actually reports, measured not assumed.

        A RAPL sub-domain the current user cannot read is simply absent from
        CodeGreen's output, so the only honest way to know what a reading
        covers is to take one.  Callers use this to check that the domains
        they asked for are the domains they are getting.
        """
        probe = self.sample(lambda: None)
        return tuple(sorted(probe.domains_j or {}))

    def missing_domains(self) -> tuple[str, ...]:
        """Requested domains with no counter behind them on this host."""
        seen = self.visible_domains()
        return tuple(
            requested
            for requested in self._domains
            if not any(name.startswith(requested) for name in seen)
        )
