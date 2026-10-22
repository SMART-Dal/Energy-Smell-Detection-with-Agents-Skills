#!/usr/bin/env python3
"""Measure the energy of any Python call, at any step, whenever you want to know.

    import sys; sys.path.insert(0, "<this skill's folder>/scripts")
    from energy import measure

    r = measure(my_function, data, sep=",")    # calls my_function(data, sep=",") once
    r.joules, r.seconds, r.watts, r.result

One call, one reading: the energy the CPU package used while the call ran, how
long it ran, and what it returned. Everything else is yours to decide: what to
run, on what data, how many times, in what order, and what the numbers mean.

The meter reads the whole machine, not this process, so a reading also holds
whatever else ran at that moment, and a call much shorter than a second is
mostly noise. Run the call in a loop inside the function you measure until a
reading lasts about a second, take several readings, put the versions you
compare in turns (before, after, before, after, ...), and compare their middle
values. That is what verify.py does.

These readings are for your own judgement, and nothing records them. A repair
is still measured by verify.py, in step 3, on the inputs generated for it.

While the inputs of a unit are being generated, a reading waits until the
generator's code has stopped running, and the generator waits for the reading,
so neither measures the other.
"""

from __future__ import annotations

import contextlib
import fcntl
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import meters  # noqa: E402
from lib.inputs import ask  # noqa: E402


@dataclass
class Reading:
    joules: float
    seconds: float
    watts: float
    domains: dict       # joules per counter read, e.g. {"package-0": ..., "package-1": ...}
    result: Any         # what the call returned


_meter = None
_locks: list[Path] | None = None


def meter():
    """RAPL when this user can read it, otherwise CodeGreen. They read the same
    counters, but CodeGreen's sampler keeps warning on stderr, for the rest of
    the process, about every counter it cannot read."""
    global _meter
    if _meter is None:
        for candidate in (meters.RaplMeter(), meters.CodeGreenMeter()):
            if candidate.available():
                _meter = candidate
                break
        else:
            raise RuntimeError("no energy meter can be read on this host")
    return _meter


@contextlib.contextmanager
def _alone():
    """The input generator's meter lock, held alone, when a generator is running
    (tools/inputs/generate.py `metering`); nothing when none is."""
    global _locks
    if _locks is None:
        answer = ask({"op": "meter_lock"}, timeout=10)
        _locks = [Path(answer["turnstile"]), Path(answer["lock"])] if answer.get("ok") else []
    with contextlib.ExitStack() as held:
        for path in _locks:
            fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o666)
            held.callback(os.close, fd)         # closing it releases the lock
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield


def measure(fn: Callable, *args, **kwargs) -> Reading:
    """Call `fn(*args, **kwargs)` once and read the energy it used.

    An exception from `fn` propagates unchanged, and there is no reading.
    """
    chosen = meter()
    returned = []
    with _alone():
        sample = chosen.sample(lambda: returned.append(fn(*args, **kwargs)))
    return Reading(sample.energy_j, sample.duration_s, sample.power_w,
                   dict(sample.domains_j or {}), returned[0])


if __name__ == "__main__":
    print(__doc__)
    print(f"meter on this host: {meter().name}")
