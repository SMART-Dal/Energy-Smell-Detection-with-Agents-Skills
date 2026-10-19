"""Child process: measure one case through both variants, print JSON samples.

Run as `python -m lib._runner <spec.json>` from the `scripts/` directory. See
`measure.py` for the spec format and the reasoning behind the design.

Both variants are measured *inside this one process*, alternating which goes
first. That is deliberate. Measuring each variant in its own process was tried
and gave substantially wider confidence intervals, because the dominant noise
source is drift in the machine's idle power between measurements -- and the
further apart in time two paired samples sit, the more drift accumulates
between them. Keeping the pair adjacent is worth more than keeping it isolated.

Interpreter startup stays outside every measured region, which is the other
thing that matters: on a many-core host, startup can cost as much energy as a
short workload.

Two warmups run before the first sample, and they warm different things. The
machine warmup (`burn_cpu`) spends `warmup_seconds` on arithmetic unrelated to
the case, so the core is at a steady clock and temperature rather than
ramping through the first windows. The code warmup then calls each variant a
few times so neither pays a one-off interpreter cost. Neither is measured.
"""

from __future__ import annotations

import gc
import json
import math
import random
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.casefile import load_case_file  # noqa: E402
from lib.meters import get_meter  # noqa: E402


def burn_cpu(seconds: float) -> float:
    """Busy the current core for `seconds` with work unrelated to any case.

    Unrelated is the point. Warming with the workload under test would populate
    caches, memo tables and branch predictors that one variant benefits from
    and the other does not, which is a bias dressed up as a warmup. Plain
    floating-point arithmetic on a seeded PRNG touches none of that, stays
    reproducible run to run, and is not something the interpreter can fold away.

    The running total is returned so nothing here can be mistaken for dead code
    and removed by a future reader.
    """
    if seconds <= 0:
        return 0.0
    rng = random.Random(0)
    deadline = time.perf_counter() + seconds
    total = 0.0
    while time.perf_counter() < deadline:
        # A chunk of work between clock reads, so the timer is not most of the
        # loop. Sized to a few milliseconds, well under the warmup budget.
        for _ in range(2000):
            total += math.sqrt(rng.random() * 1e6) % 7.0
    return total


POOL_LIMIT_S = 5.0
"""Longest a pool of fresh arguments may take to build, before one window."""

POOL_LIMIT_BYTES = 2 << 30
"""Most memory a pool of fresh arguments may take."""


class PoolTooLarge(RuntimeError):
    """Every call in a window gets a fresh set of arguments, and these are too
    costly to build that many times."""


def _traced(make):
    """make()'s result, and the bytes it allocated that are still held."""
    if tracemalloc.is_tracing():
        return make(), 0
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        made = make()
        return made, max(0, tracemalloc.get_traced_memory()[0] - before)
    finally:
        tracemalloc.stop()


def build_pool(make, size: int) -> list:
    """`size` results of `make()`: the arguments for the measured loop, built outside it.

    One set per call: the window repeats the call only to give the meter
    enough energy to read, so every call starts from the input as the thunk
    builds it. Nothing a call does to its arguments -- sorting, filling,
    emptying them -- reaches the next call, and a thunk that makes new keys
    each time keeps a cache outside them from answering the next call either.

    Repeat counts are large when one call is cheap, and that usually means
    small arguments too -- but not always: a call that looks one key up in a
    large dict is cheap with arguments that are not. So the pool
    is projected from what the first sets cost -- the memory of the first set,
    traced; the time of the sets after it, checked at 1, 2, 4, ... more once
    they have taken long enough to time -- and refused once the projection
    passes either limit: before the machine runs out of memory, not after.
    """
    if size <= 1:
        return [make() for _ in range(size)]
    first, held = _traced(make)
    pool, memory, seconds = [first], held * size, 0.0
    started, batch = time.perf_counter(), 1
    while len(pool) < size:
        if time.perf_counter() - started < 0.05:
            seconds = 0.0           # a few microseconds time the clock, not the build
        over = ([f"{memory / 1e9:,.1f} GB (limit {POOL_LIMIT_BYTES / 1e9:.1f} GB)"]
                if memory > POOL_LIMIT_BYTES else []) + \
               ([f"about {seconds:,.0f}s (limit {POOL_LIMIT_S:g}s)"] if seconds > POOL_LIMIT_S else [])
        if over:
            raise PoolTooLarge(
                f"each of the {size:,} calls in a window gets fresh arguments, "
                f"and building them would take "
                f"{' and '.join(over)}: one call does too little work for arguments that size")
        for _ in range(min(batch, size - len(pool))):
            pool.append(make())
        batch *= 2
        seconds = (time.perf_counter() - started) / (len(pool) - 1) * size
    return pool


def run_window(function, pool: list[tuple], repeats: int) -> None:
    """The measured region: `repeats` calls, and nothing else.

    Deliberately dull. Anything done here is charged to the variant, so index
    arithmetic is kept to a single modulo and the return values are dropped
    without inspection.
    """
    size = len(pool)
    for index in range(repeats):
        function(*pool[index % size])


def main(argv: list[str]) -> int:
    spec = json.loads(Path(argv[1]).read_text())

    # No affinity is set. The meter reports whole-machine energy across every
    # package, so a thread that migrates is still fully measured, and pinning
    # to one core holds the workload on a single thread of a single socket
    # while the rest of the machine idles into the same reading.
    meter = get_meter(spec["meter"])
    case_file = load_case_file(Path(spec["case_file"]))
    case = next(c for c in case_file.cases if c.label == spec["label"])

    repeats = spec["repeats"]
    variants = [(label, case_file.variant(attr)) for label, attr in spec["variants"]]

    # Warm the machine first: bring the clock and temperature to a steady
    # state before anything is measured, so the climb out of idle is not
    # charged to whichever variant happens to be measured first.
    burn_cpu(spec.get("warmup_seconds", 0.0))

    # Then warm the code, so neither variant pays the one-off cost of
    # import-time laziness, bytecode caching or the first allocation of a new
    # size class.
    warm = min(repeats, spec.get("warmup_calls", 1))
    for _, function in variants:
        run_window(function, build_pool(case.args, warm), warm)

    samples = []
    for rep in range(spec["reps"]):
        # Alternate order each repetition so systematic drift is shared evenly
        # between the variants instead of charged to whichever runs second.
        ordered = variants if rep % 2 == 0 else variants[::-1]
        for label, function in ordered:
            # A fresh pool before every window, outside the measured region:
            # the window before it used every set up, and is freed first.
            pool = None
            pool = build_pool(case.args, repeats)
            gc.collect()
            sample = meter.sample(lambda: run_window(function, pool, repeats))
            samples.append({
                "label": label,
                "rep": rep,
                "energy_j": sample.energy_j,
                "duration_s": sample.duration_s,
                "power_w": sample.power_w,
                "domains": sorted(sample.domains_j or {}),
            })

    print(json.dumps(samples))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
