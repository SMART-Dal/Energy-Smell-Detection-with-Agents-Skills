"""The types the measurement half passes around.

    verify.py   Sample  -> Comparison       what the machine measured

Frozen dataclasses throughout, so an intermediate result can be printed and
compared without surprises.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    """A single execution: how much energy it took and how long it ran.

    `energy_j` and `duration_s` are the two fields the statistics are built
    from.  The rest is provenance -- what the meter saw while taking the
    reading -- carried so a result can be audited without re-running it.
    """

    energy_j: float
    duration_s: float
    power_w: float = 0.0
    """Average watts over the window; `energy_j / duration_s` by construction."""
    domains_j: dict[str, float] | None = None
    """Per-domain energy the host exposed. Not disjoint, and not summed -- see
    `meters/codegreen_meter.py`. Present so a row records its own coverage."""
    quality: str | None = None
    """Meter's own noise verdict, when it computed one: excellent/good/
    moderate/high-noise. `None` unless time series recording was enabled."""
    power_cv_pct: float | None = None
    """Coefficient of variation of power within the window, same caveat."""


@dataclass(frozen=True)
class Comparison:
    """Result of a paired A/B energy experiment (original vs patched).

    Deltas are expressed as "how much the patched version saves", so a positive
    `energy_saved_pct` means the patch helped.
    """

    baseline_energy_j: float
    patched_energy_j: float
    baseline_duration_s: float
    patched_duration_s: float
    energy_saved_pct: float
    energy_ci_pct: float
    """Half-width of the 95% confidence interval on `energy_saved_pct`."""
    time_saved_pct: float
    time_ci_pct: float
    reps: int
    domains: tuple[str, ...] = ()
    """Energy domains the meter actually reported over these windows. Taken
    from the readings themselves rather than probed separately, so it cannot
    disagree with the numbers it sits beside."""
    baseline_power_w: float = 0.0
    patched_power_w: float = 0.0
    """Mean watts over the measured windows. Reported because a repair can cut
    energy by finishing sooner, by drawing less, or both, and only the pair of
    energy and power tells those apart."""

    @property
    def energy_significant(self) -> bool:
        """True when the confidence interval excludes zero."""
        return abs(self.energy_saved_pct) > self.energy_ci_pct

    @property
    def time_significant(self) -> bool:
        return abs(self.time_saved_pct) > self.time_ci_pct

    @property
    def energy_only(self) -> bool:
        """Energy improved but wall-clock time did not: the interesting case.

        These are the instances that distinguish an *energy* effect from a mere
        performance one, so they are surfaced explicitly in reports.
        """
        return self.energy_significant and not self.time_significant
