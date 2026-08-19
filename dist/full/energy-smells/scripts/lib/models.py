"""The types the measurement half passes around.

    verify.py   Sample  -> Comparison       what the machine measured

Frozen dataclasses throughout, so an intermediate result can be printed and
compared without surprises.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    """A single execution: how much energy it took and how long it ran."""

    energy_j: float
    duration_s: float


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
