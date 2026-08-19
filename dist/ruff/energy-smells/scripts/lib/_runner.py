"""Child process: measure one case through both variants, print JSON samples.

Run as `python -m lib._runner <spec.json>` from the `scripts/` directory. See
`measure.py` for the spec format and the reasoning behind the design.

Both variants are measured *inside this one process*, alternating which goes
first. That is deliberate. Measuring each variant in its own process was tried
and gave roughly 3.5x wider confidence intervals on the development host,
because the dominant noise source is drift in the machine's idle power between
measurements -- and the further apart in time two paired samples sit, the more
drift accumulates between them. Keeping the pair adjacent is worth more than
keeping it isolated.

Interpreter startup stays outside every measured region, which is the other
thing that matters: on a 24-core host, startup costs about as much energy as a
short workload.
"""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.casefile import load_case_file  # noqa: E402
from lib.meters import get_meter  # noqa: E402


def build_pool(case, size: int) -> list[tuple]:
    """Argument tuples to feed the measured loop, built outside it.

    A variant that mutates its arguments needs a fresh tuple per iteration, or
    the workload changes shape as the loop runs. One that does not can reuse a
    single tuple, which keeps memory flat and the garbage collector quiet.

    The pool costs less than it looks: repeat counts are large exactly when the
    inputs are small, because both are set by how long one call takes.
    """
    return [case.args() for _ in range(size)]


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

    # Pin to one core so the workload is not migrated mid-measurement, which
    # would attribute another core's activity to us.
    cpu = spec.get("cpu", -1)
    if cpu >= 0 and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {cpu})

    meter = get_meter(spec["meter"])
    case_file = load_case_file(Path(spec["case_file"]))
    case = next(c for c in case_file.cases if c.label == spec["label"])

    repeats = spec["repeats"]
    variants = [(label, case_file.variant(attr)) for label, attr in spec["variants"]]
    pool = build_pool(case, repeats if spec.get("mutates") else 1)

    # Warm up both variants so neither pays the one-off cost of import-time
    # laziness, bytecode caching or the first allocation of a new size class.
    for _, function in variants:
        run_window(function, pool, min(repeats, spec.get("warmup_calls", 1)))

    samples = []
    for rep in range(spec["reps"]):
        # Alternate order each repetition so systematic drift is shared evenly
        # between the variants instead of charged to whichever runs second.
        ordered = variants if rep % 2 == 0 else variants[::-1]
        for label, function in ordered:
            gc.collect()
            sample = meter.sample(lambda: run_window(function, pool, repeats))
            samples.append({
                "label": label,
                "rep": rep,
                "energy_j": sample.energy_j,
                "duration_s": sample.duration_s,
            })

    print(json.dumps(samples))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
