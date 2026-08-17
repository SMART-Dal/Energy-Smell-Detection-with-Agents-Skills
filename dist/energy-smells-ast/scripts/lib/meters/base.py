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

# Energy domains we count by default.  The CPU package and its DRAM are what
# Python workloads actually move; an idle GPU still reports several watts, and
# including it only dilutes the effect we are trying to resolve.
DEFAULT_DOMAINS = ("package", "dram")


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
