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

import atexit
import contextlib
import fcntl
import os
import subprocess
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
    """The meter verify.py measures with: CodeGreen, or raw RAPL without it."""
    global _meter
    if _meter is None:
        chosen = meters.get_meter("auto")
        if not chosen.available():
            raise RuntimeError("no energy meter can be read on this host")
        if chosen.name == "codegreen":
            _quiet_codegreen()
        _meter = chosen
    return _meter


CODEGREEN_NOISE = "Missing raw value for active counter"


def _quiet_codegreen() -> None:
    """Drop CodeGreen's warnings from stderr, and nothing else.

    Once it has taken a reading, CodeGreen's sampler, in its native library,
    writes a line to file descriptor 2 for each counter this user cannot read
    (here `core` and `dram`; `package` is what it measures), every millisecond,
    for the rest of the process: 5,420 lines in 3 s. So file descriptor 2
    becomes a pipe into `grep -v`, which passes every other line on to the real
    stderr -- this process's own, and that of anything it starts. A process,
    not a thread: a thread here would take the interpreter lock from the code
    being measured every time the sampler writes.
    """
    read, write = os.pipe()
    sys.stderr.flush()
    sieve = subprocess.Popen(["grep", "--line-buffered", "-v", "-F", CODEGREEN_NOISE],
                             stdin=read, stdout=2, stderr=2)
    os.close(read)
    os.dup2(write, 2)
    os.close(write)

    def drain():
        # At exit, the sampler's later writes go nowhere, and grep passes on
        # what is still in the pipe before this process ends.
        sys.stderr.flush()
        nothing = os.open(os.devnull, os.O_WRONLY)
        os.dup2(nothing, 2)
        os.close(nothing)
        with contextlib.suppress(subprocess.TimeoutExpired):
            sieve.wait(timeout=1)

    atexit.register(drain)


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
