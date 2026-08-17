"""Paired A/B energy measurement: does this repair actually save energy?

The design follows rules established by experiment on the development host, not
by taste. Three of them matter enough to state up front.

**Interleave, and keep the pair close together in time.** The dominant noise
source is drift in the machine's idle power, so paired samples must sit next to
each other. Measuring each variant in a separate process widened confidence
intervals about 3.5x compared with alternating both inside one process.

**Scale the workload, not the repetition count.** A window too short to
average over its surroundings cannot be rescued by measuring it more often: at
a quarter-second window the canary interval was +-8.1%, and at one second it
was +-0.6%. This is why `verify.py` sizes every case to a full window before
measuring it, however small the case itself is.

**Calibrate against a null canary rather than trusting a fixed threshold.**
Comparing a variant against an identical copy must come back insignificant. How
wide that null interval is depends entirely on the host, so `noise_floor()`
measures it and callers set their decision threshold from the result.

A note on what is being measured
--------------------------------
The meter reports CPU package + DRAM energy over the workload window. On a
many-core host most of that is idle power from cores doing nothing: the
development machine idles at 47.3 W and one busy Python thread takes it to
55.4 W, so only about an eighth of any reading is work we caused.

That sounds fatal and is not, because the window is not a fixed length. A
variant that finishes sooner accrues less idle power too, so *system energy
over the window* scales with how long the work took, and a repair that cuts a
third of the work shows up as roughly a third less energy rather than an eighth
of that. What the figure will not do is separate a change in power draw from a
change in duration.

Subtracting a calibrated idle baseline to recover "attributable" energy was
tried and rejected: it amplifies relative noise so badly that a real 24% effect
stopped being significant (+-16.6% intervals).

Time is recorded separately, so the cases where energy and duration diverge --
the ones that distinguish an energy effect from a performance one -- stay
visible.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

from .models import Comparison

DEFAULT_REPS = 9
DEFAULT_WARMUP_CALLS = 1

TARGET_WINDOW_S = 1.0
"""How long one measured window should last.

Chosen by sweeping the null canary on the development host, not by taste. At
nine paired repetitions the canary interval came out:

    0.25 s window   +-8.13%
    0.50 s          +-1.70%
    1.00 s          +-0.63%
    2.00 s          +-0.84%

Short windows lose because a paired sample is dominated by whatever the machine
did in the surrounding milliseconds. Past a second there is nothing left to
gain, and doubling the window only doubles the run time and the chance that
some other process wanders through the measurement.
"""

MAX_REPEATS = 20_000_000
"""Ceiling on the repeat count, so a mis-sized case cannot run forever."""

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


class MeasurementError(RuntimeError):
    """A variant failed to run, so no comparison is possible."""


def choose_repeats(seconds_per_call: float, target: float = TARGET_WINDOW_S) -> int:
    """How many calls make one measured window long enough to trust.

    This is the answer to "short test cases are all noise": a 40 microsecond
    edge case is simply run fifty thousand times. The agent writes each case at
    its natural size and never reasons about noise floors.
    """
    if seconds_per_call <= 0:
        return MAX_REPEATS
    return max(1, min(MAX_REPEATS, int(target / seconds_per_call) + 1))


def compare_case(
    case_path: Path,
    label: str,
    *,
    repeats: int,
    mutates: bool = False,
    variants: tuple[tuple[str, str], ...] = (("before", "before"), ("after", "after")),
    reps: int = DEFAULT_REPS,
    meter: str = "auto",
    cpu: int = 0,
) -> Comparison:
    """Measure how much energy `after` saves relative to `before` on one case.

    `variants` maps a reporting label to the function to call. The default
    compares the two variants; passing the same function under both labels is
    how `noise_floor()` builds its null canary.

    Savings are computed per repetition and then averaged, so each percentage
    comes from two samples taken moments apart under near-identical machine
    conditions.
    """
    samples = _execute({
        "case_file": str(case_path.resolve()),
        "label": label,
        "variants": [list(v) for v in variants],
        "repeats": repeats,
        "mutates": mutates,
        "reps": reps,
        "warmup_calls": DEFAULT_WARMUP_CALLS,
        "meter": meter,
        "cpu": cpu,
    })
    return _summarise(samples, reps=reps)


def noise_floor(case_path: Path, label: str, **kwargs) -> Comparison:
    """Compare `before` against itself: the null canary.

    The result should be insignificant. Its confidence interval is this host's
    resolution limit for this workload, and callers should require real effects
    to clear it. A canary that comes back *significant* means the machine is
    too noisy to trust and the batch should be discarded.
    """
    return compare_case(
        case_path,
        label,
        variants=(("before", "before"), ("after", "before")),
        **kwargs,
    )


# -- running the child process ---------------------------------------------


def _execute(spec: dict) -> list[dict]:
    """Run one measurement block in a child process and read back its samples."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(spec, handle)
        spec_path = Path(handle.name)
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "lib._runner", str(spec_path)],
            capture_output=True,
            text=True,
            cwd=SCRIPTS_DIR,
        )
    finally:
        spec_path.unlink(missing_ok=True)

    if completed.returncode != 0:
        raise MeasurementError(
            "the measurement subprocess failed:\n"
            + completed.stderr.strip()[-2000:]
        )
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise MeasurementError(
            f"the measurement produced no samples: {completed.stdout!r}"
        ) from exc


# -- statistics ------------------------------------------------------------


def _summarise(samples: list[dict], *, reps: int) -> Comparison:
    by_rep: dict[int, dict[str, dict]] = {}
    for sample in samples:
        by_rep.setdefault(sample["rep"], {})[sample["label"]] = sample

    energy_savings, time_savings = [], []
    before_energy, after_energy = [], []
    before_time, after_time = [], []

    for pair in by_rep.values():
        before, after = pair["before"], pair["after"]
        before_energy.append(before["energy_j"])
        after_energy.append(after["energy_j"])
        before_time.append(before["duration_s"])
        after_time.append(after["duration_s"])
        if before["energy_j"] > 0:
            energy_savings.append(
                100.0 * (before["energy_j"] - after["energy_j"]) / before["energy_j"]
            )
        if before["duration_s"] > 0:
            time_savings.append(
                100.0 * (before["duration_s"] - after["duration_s"]) / before["duration_s"]
            )

    energy_mean, energy_ci = _mean_and_ci(energy_savings)
    time_mean, time_ci = _mean_and_ci(time_savings)

    return Comparison(
        baseline_energy_j=statistics.mean(before_energy),
        patched_energy_j=statistics.mean(after_energy),
        baseline_duration_s=statistics.mean(before_time),
        patched_duration_s=statistics.mean(after_time),
        energy_saved_pct=energy_mean,
        energy_ci_pct=energy_ci,
        time_saved_pct=time_mean,
        time_ci_pct=time_ci,
        reps=reps,
    )


# Two-sided 95% critical values of Student's t, by degrees of freedom. A small
# table beats a SciPy dependency for the handful of repetition counts we use,
# and keeps the skill on the standard library.
_T_CRITICAL_95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
    7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
    13: 2.160, 14: 2.145, 15: 2.131, 20: 2.086, 30: 2.042,
}


def _t_critical(degrees_of_freedom: int) -> float:
    if degrees_of_freedom < 1:
        return float("inf")
    if degrees_of_freedom in _T_CRITICAL_95:
        return _T_CRITICAL_95[degrees_of_freedom]
    if degrees_of_freedom >= 30:
        return 1.960
    return _T_CRITICAL_95[max(k for k in _T_CRITICAL_95 if k < degrees_of_freedom)]


def _mean_and_ci(values: list[float]) -> tuple[float, float]:
    """Sample mean and the half-width of its 95% confidence interval."""
    if not values:
        return 0.0, float("inf")
    if len(values) < 2:
        return values[0], float("inf")
    standard_error = statistics.stdev(values) / (len(values) ** 0.5)
    return statistics.mean(values), _t_critical(len(values) - 1) * standard_error
