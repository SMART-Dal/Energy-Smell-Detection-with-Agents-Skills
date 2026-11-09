"""The one abstraction in this codebase: how to measure energy.

There are three real implementations (CodeGreen, raw RAPL, and a deterministic
fake for tests), which is why this is a protocol rather than a concrete class.
Resist adding more abstractions elsewhere.

A meter measures a callable *in the current process*.  That matters: process
startup costs roughly as much energy as a whole short workload, so it must sit
outside the measured region.  The A/B harness therefore spawns a subprocess per
variant and has the child measure only its own workload (see `measure.py`).
"""

from __future__ import annotations

from typing import Callable, Protocol, runtime_checkable

from ..models import Sample

# Energy domains a reading is expected to cover.  The CPU package is where
# Python workloads spend, and it is the one domain every host with RAPL
# exposes; DRAM is a separate counter that many hosts do not let a normal user
# read, and a Python workload moves little enough memory that its absence does
# not change a verdict.
#
# This list is what `missing_domains()` is checked against, not a filter: the
# reported figure is the meter's own total, and nothing is subtracted from it
# -- no idle baseline, no attribution to this process.  See measure.py for why.
DEFAULT_DOMAINS = ("package",)


@runtime_checkable
class EnergyMeter(Protocol):
    """Measures the energy and wall-clock cost of running a callable."""

    name: str

    def sample(self, fn: Callable[[], object]) -> Sample:
        """Run `fn` once and report what it cost.

        Implementations must exclude their own overhead from the reported
        numbers as far as possible, and must not raise when the workload
        raises -- callers rely on exceptions propagating unchanged.
        """
        ...

    def available(self) -> bool:
        """Whether this meter can actually take readings on this machine."""
        ...
