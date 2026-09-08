"""CodeGreen-backed meter -- the default on supported hardware.

CodeGreen (Rajput & Sharma, 2026) polls hardware sensors from a native backend
and reports per-domain energy, which is more portable than reading RAPL sysfs
directly (it also covers macOS and Windows).

The numbers come from the session's `totals` block, which is the figure
CodeGreen itself reports for a run.  Two consequences of how CodeGreen works
shape this class:

*A session must contain a task.*  A session that starts and stops with no task
inside it writes no report at all, so the workload is wrapped in one.  With a
single task, `totals.energy_j` and that task's `energy_j` are the same value to
the last digit; `totals` is used anyway because it is the documented aggregate
and carries the run's duration accounting alongside.

*`totals` exists only in the output file.*  The Session object exposes no
in-memory equivalent, so each sample writes a small JSON report to a scratch
file and reads it back.  That write happens inside `stop()`, after the measured
task has ended, so it is not charged to the workload.

`totals.energy_j` is taken as it comes.  It is not re-derived from the
per-domain breakdown, because that breakdown is deliberately not disjoint -- on
Intel the package domain already contains `core`/`pp0` -- and summing it
double-counts.  Nothing is subtracted from the reading either: no idle
baseline, no attribution to this process.  See `measure.py` for why.
"""

from __future__ import annotations

import atexit
import json
import shutil
import tempfile
from pathlib import Path
from typing import Callable

from ..models import Sample
from .base import DEFAULT_DOMAINS


class CodeGreenMeter:
    """Measures energy via a CodeGreen session with a single task."""

    name = "codegreen"

    def __init__(self, domains: tuple[str, ...] = DEFAULT_DOMAINS):
        self._domains = domains
        self._scratch: str | None = None
        try:
            import codegreen

            self._codegreen = codegreen
        except ImportError:
            self._codegreen = None

    def available(self) -> bool:
        return self._codegreen is not None

    def _report_path(self) -> Path:
        """One scratch file, rewritten per sample, removed with the process."""
        if self._scratch is None:
            self._scratch = tempfile.mkdtemp(prefix="energy-verify-")
            # A batch spawns a subprocess per case file, so a scratch
            # directory left behind by each one adds up quickly.
            atexit.register(self.close)
        return Path(self._scratch) / "report.json"

    def sample(self, fn: Callable[[], object]) -> Sample:
        if self._codegreen is None:
            raise RuntimeError("codegreen is not installed; pip install codegreen")

        report = self._report_path()
        session = self._codegreen.Session(
            "energy-verify",
            output_file=str(report),
            output_format="json",
            warn_on_concurrent=False,
        )
        session.start()
        session.start_task("workload")
        try:
            fn()
        finally:
            session.stop_task()
            session.stop()

        if not report.exists():
            raise RuntimeError(
                "codegreen wrote no report for this window; the backend is "
                "probably not loaded (check `codegreen --version`)"
            )
        document = json.loads(report.read_text())
        totals = document.get("totals") or {}
        meta = document.get("meta") or {}

        energy_j = totals.get("energy_j", 0.0)
        # `duration_s` is the summed task time, which is the window `energy_j`
        # was accumulated over. `wall_duration_s` also counts the gap outside
        # the task and would not divide into the energy correctly.
        duration_s = totals.get("duration_s") or totals.get("task_duration_s") or 0.0
        return Sample(
            energy_j=energy_j,
            duration_s=duration_s,
            power_w=energy_j / duration_s if duration_s > 0 else 0.0,
            domains_j=dict(totals.get("domains") or {}),
            quality=meta.get("measurement_quality"),
        )

    def close(self) -> None:
        if self._scratch:
            shutil.rmtree(self._scratch, ignore_errors=True)
            self._scratch = None

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
