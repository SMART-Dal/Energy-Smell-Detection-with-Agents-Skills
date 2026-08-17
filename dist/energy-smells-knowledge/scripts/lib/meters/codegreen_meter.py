"""CodeGreen-backed meter -- the default on supported hardware.

CodeGreen (Rajput & Sharma, 2026) polls hardware sensors from a native backend
and reports per-domain energy, which is more portable than reading RAPL sysfs
directly (it also covers macOS and Windows).  We use its in-memory `TaskResult`
rather than its JSON output files, and sum only the domains we care about.
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
            session.stop()

        result = session.tasks[-1]
        return Sample(
            energy_j=self._sum_domains(result),
            duration_s=result.duration_s,
        )

    def _sum_domains(self, result) -> float:
        """Total only the requested domains.

        `result.energy_j` includes every domain the backend saw, GPU included.
        On a CPU-bound Python workload an idle GPU contributes a constant few
        joules that shrinks every measured effect size, so we select explicitly
        and fall back to the reported total only if nothing matched.
        """
        domains = getattr(result, "domains", None) or {}
        selected = sum(
            joules
            for domain, joules in domains.items()
            if any(domain.startswith(prefix) for prefix in self._domains)
        )
        return selected if selected > 0 else result.energy_j
