#!/usr/bin/env python3
"""Prove a repair saves energy, or find out that it does not.

    python verify.py cases/my_case.py            readable report
    python verify.py cases/my_case.py --json     for findings.json
    python verify.py --calibrate                    this host's noise floor

A case file supplies `before`, `after` and `cases()`; see reference/verifying.md
for the contract. This script then does four things, in order:

    1. equivalence   `after` must behave exactly like `before` on every case
    2. sizing        each case is repeated until its window lasts ~3 seconds
    3. measurement   the two variants alternate inside one process, 9 paired reps
    4. the canary    `before` against itself, to bound what this host can resolve

The verdict is the point, and there are five of them:

    confirmed     every case that moved, moved the right way
    mixed         helps some inputs, hurts others -- a trade-off
    regressed     every case that moved, got worse
    negligible    measured cleanly; nothing moved more than the noise
    inconclusive  this host could not resolve an effect of this size

`negligible` is the analysis working, not failing: the repair was built and
measured and does nothing. `inconclusive` is the opposite -- it says nothing
about the code, only that the machine was too noisy to ask. Collapsing those
two is how a busy host gets recorded as evidence against a repair.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import equivalence  # noqa: E402
from lib.casefile import Case, CaseFile, CaseFileError, load_case_file  # noqa: E402
from lib.measure import (  # noqa: E402
    DEFAULT_REPS,
    TARGET_WINDOW_S,
    MeasurementError,
    choose_repeats,
    compare_case,
    noise_floor,
)
from lib import meters  # noqa: E402
from lib.models import Comparison  # noqa: E402

CANARY_CASE = Path(__file__).resolve().parent / "lib" / "canary_case.py"

REGRESSION_TOLERANCE_PCT = 1.0
"""When a loss on one case is big enough to sink an otherwise good repair.

Measured as a percentage of the *deciding* case's per-call cost, not of the
case's own. That distinction is the whole rule. Joining an empty list costs a
microsecond or so where returning `""` costs a fraction of one, so on an empty
case the repair measures as several times worse -- a true statement about a
quantity nobody cares about. Weighted against a deciding case running in
milliseconds, the same loss rounds to nothing and is correctly ignored.

A repair that costs 20% on a case a tenth the size of the deciding one is a
different matter: that is 2% of real work, it clears this bar, and the verdict
calls it a trade-off.

This is one of two bars. The loss must also clear the host's noise floor, for
the same reason a saving must. See `_harmful_cases`.
"""

TIMING_CALLS = 5
"""Calls used to estimate per-call cost. Enough to avoid a cold-start outlier."""

SLOW_WINDOW_BUDGET_S = 15.0
"""Ceiling on the slower variant's measured window.

Repeats are chosen so the *faster* variant fills a full window, and both
variants then run that same count -- equal work on both sides is what makes the
comparison fair. When one variant is far slower, that same count makes its
window longer by exactly the ratio between them, and a repair that is a
thousand times slower would be measured for a thousand times as long.

So the count is clamped to keep the slow side inside this budget, which means
the fast side gets less than a full window. That is safe, and the reason is
worth stating because it looks like a compromise and is not:

A full window exists to stop noise swamping a *small* difference. A small
difference means the two variants run at similar speeds, the ratio is near one,
and nothing is clamped. Clamping only happens when the ratio is enormous -- and
then the saving is enormous too, and the answer is set by the large, well
resolved side. With a 30 s window against a 3 ms one, the reading is 1500 J
against 0.15 J; even if the tiny side is wrong by a factor of two, the saving
moves from 99.99% to 99.98%.

The two conditions cannot bite at once. The more the clamp costs in window
length, the less that length matters.
"""

REDUCED_REPS = 3
"""Paired repetitions used when a single call already exceeds the budget.

At that point the effect is far past anything a confidence interval needs to
separate from zero, and nine repetitions of a window that cannot be shortened
is most of an hour for one case."""

USABLE_FLOOR_PCT = 3.0
"""Above this canary reading, a null result means nothing and says so.

This is a policy bar, not a property of any particular machine: it is the point
past which "the repair saves nothing" stops being a claim the data supports,
because effects smaller than the host's own noise cannot be distinguished from
zero. A quiet host sits far below it; a host with another user on it can sit an
order of magnitude above, and every null verdict measured in that band is an
artefact of the machine rather than a fact about the code.

The floor itself is never assumed -- `verify()` measures it per run with the
canary, and `--calibrate` reports it on its own. When moving to a new machine,
calibrate first: if its quiet floor is not comfortably under this bar, the
problem is the host, not the threshold, and raising the threshold only hides it.
"""


# -- results ---------------------------------------------------------------


@dataclass
class CaseOutcome:
    """Everything measured about one case."""

    label: str
    equivalent: bool
    difference: str = ""
    mutates_args: bool = False
    seconds_per_call: float = 0.0
    before_spc: float = 0.0
    after_spc: float = 0.0
    """Per-call cost of each variant, measured before sizing. The faster of the
    two sets the repeat count; the ratio between them says how lopsided the
    case is, and whether the count had to be clamped."""
    repeats: int = 0
    reps: int = DEFAULT_REPS
    clamped: bool = False
    """True when the repeat count was cut to keep the slow side affordable, so
    the fast side got less than a full window. The reading is still sound --
    see SLOW_WINDOW_BUDGET_S -- but the row should say so."""
    baseline_window_s: float = 0.0
    patched_window_s: float = 0.0
    """What the measured windows actually came out at, as opposed to what they
    were sized for. Recorded because the two silently diverging is exactly the
    failure this sizing rewrite exists to prevent."""
    energy_saved_pct: float = 0.0
    energy_ci_pct: float = 0.0
    time_saved_pct: float = 0.0
    time_ci_pct: float = 0.0
    significant: bool = False
    energy_only: bool = False
    baseline_energy_j: float = 0.0
    baseline_power_w: float = 0.0
    patched_power_w: float = 0.0
    before_s_per_call: float = 0.0
    after_s_per_call: float = 0.0

    def record(self, comparison: Comparison) -> None:
        self.energy_saved_pct = comparison.energy_saved_pct
        self.energy_ci_pct = comparison.energy_ci_pct
        self.time_saved_pct = comparison.time_saved_pct
        self.time_ci_pct = comparison.time_ci_pct
        self.significant = comparison.energy_significant
        self.energy_only = comparison.energy_only
        self.baseline_energy_j = comparison.baseline_energy_j
        self.baseline_power_w = comparison.baseline_power_w
        self.patched_power_w = comparison.patched_power_w
        self.baseline_window_s = comparison.baseline_duration_s
        self.patched_window_s = comparison.patched_duration_s
        self.before_s_per_call = comparison.baseline_duration_s / self.repeats
        self.after_s_per_call = comparison.patched_duration_s / self.repeats

    @property
    def excess_s_per_call(self) -> float:
        """Extra time `after` costs per call. Negative when the repair helps."""
        return self.after_s_per_call - self.before_s_per_call


@dataclass
class Verification:
    """The verdict, and everything it was derived from."""

    case_file: str
    status: str = "negligible"
    reason: str = ""
    deciding_case: str = ""
    noise_floor_pct: float = 0.0
    reps: int = DEFAULT_REPS
    per_case: list[CaseOutcome] = field(default_factory=list)
    relaxations: tuple[str, ...] = ()
    """Ways this case file weakened the equivalence check, if any."""
    coverage: dict = field(default_factory=dict)
    """Which meter took the readings and which energy domains it could see."""

    def note_coverage(self, meter: str, domains: tuple[str, ...], log) -> None:
        """Record what the readings covered, and say so once if it fell short.

        A RAPL domain the current user cannot read is skipped in silence by
        every meter, quietly narrowing a reading from "package + DRAM" to
        whatever happened to be readable. That narrowing is invisible in the
        numbers themselves, and a batch runs for hours, so it is recorded
        beside every verdict and announced the first time it is seen.
        """
        if self.coverage:
            return
        missing = [
            requested
            for requested in meters.DEFAULT_DOMAINS
            if not any(name.startswith(requested) for name in domains)
        ]
        self.coverage = {
            # Resolve "auto" to what actually ran. Constructing a meter only
            # checks availability; it does not open a measurement session.
            "meter": meters.get_meter(meter).name,
            "requested_domains": list(meters.DEFAULT_DOMAINS),
            "visible_domains": list(domains),
            "missing_domains": missing,
        }
        if missing:
            log(f"  WARNING: no counter for {', '.join(missing)} on this host; "
                f"readings cover {', '.join(domains) or 'nothing'} only")

    @property
    def deciding(self) -> CaseOutcome | None:
        return next((c for c in self.per_case if c.label == self.deciding_case), None)

    def to_dict(self) -> dict:
        deciding = self.deciding
        return {
            "status": self.status,
            "reason": self.reason,
            "case_file": self.case_file,
            "cases_checked": len(self.per_case),
            "deciding_case": self.deciding_case,
            "repeats": deciding.repeats if deciding else 0,
            "energy_saved_pct": round(deciding.energy_saved_pct, 2) if deciding else 0.0,
            "energy_ci_pct": round(deciding.energy_ci_pct, 2) if deciding else 0.0,
            "time_saved_pct": round(deciding.time_saved_pct, 2) if deciding else 0.0,
            "time_ci_pct": round(deciding.time_ci_pct, 2) if deciding else 0.0,
            "energy_only": deciding.energy_only if deciding else False,
            "noise_floor_pct": round(self.noise_floor_pct, 2),
            "reps": self.reps,
            "equivalence_relaxed": list(self.relaxations),
            "coverage": self.coverage,
            "per_case": [
                {
                    "label": case.label,
                    "repeats": case.repeats,
                    "energy_saved_pct": round(case.energy_saved_pct, 2),
                    "energy_ci_pct": round(case.energy_ci_pct, 2),
                    "significant": case.significant,
                    "reps": case.reps,
                    "clamped": case.clamped,
                    "before_s_per_call": case.before_spc,
                    "after_s_per_call": case.after_spc,
                    "before_window_s": round(case.baseline_window_s, 3),
                    "after_window_s": round(case.patched_window_s, 3),
                    "baseline_power_w": round(case.baseline_power_w, 2),
                    "patched_power_w": round(case.patched_power_w, 2),
                }
                for case in self.per_case
            ],
        }


# -- the pipeline ----------------------------------------------------------


def verify(
    case_path: Path,
    *,
    reps: int = DEFAULT_REPS,
    meter: str = "auto",
    window: float = TARGET_WINDOW_S,
    canary: bool = True,
    log=print,
) -> Verification:
    """Run the four stages and return a verdict."""
    case_file = load_case_file(case_path)
    result = Verification(
        case_file=str(case_path), reps=reps, relaxations=case_file.relaxations
    )

    log("equivalence")
    for note in result.relaxations:
        log(f"  RELAXED: {note}")
    for case in case_file.cases:
        checked = equivalence.check(case_file, case)
        outcome = CaseOutcome(
            label=case.label,
            equivalent=checked.equivalent,
            difference=checked.difference,
            mutates_args=checked.mutates_args,
        )
        result.per_case.append(outcome)
        note = " (mutates its arguments: fresh input per call)" if checked.mutates_args else ""
        log(f"  {case.label:<12} {'ok' if checked.equivalent else 'DIFFERS'}{note}")
        if not checked.equivalent:
            log(f"  {'':<12} {checked.difference}")

    broken = [c for c in result.per_case if not c.equivalent]
    if broken:
        result.status = "not_equivalent"
        result.reason = (
            f"`after` behaves differently on {broken[0].label!r}: "
            f"{broken[0].difference}. The repair is wrong; fix it and re-run. "
            f"Do not report this candidate either way."
        )
        return result

    log("\nsizing")
    for case, outcome in zip(case_file.cases, result.per_case):
        outcome.before_spc = _time_one_call(case_file, case, case_file.before)
        outcome.after_spc = _time_one_call(case_file, case, case_file.after)
        outcome.seconds_per_call = max(outcome.before_spc, outcome.after_spc)
        outcome.repeats, outcome.reps, outcome.clamped = _size(
            outcome.before_spc, outcome.after_spc, window, reps
        )
        note = f"  CLAMPED to keep the slow side under {SLOW_WINDOW_BUDGET_S:g}s" \
            if outcome.clamped else ""
        log(f"  {case.label:<12} before {_duration(outcome.before_spc):>10}/call"
            f"  after {_duration(outcome.after_spc):>10}/call"
            f"  ->  {outcome.repeats:,} repeats{note}")

    result.deciding_case = max(result.per_case, key=lambda c: c.seconds_per_call).label

    log(f"\nmeasurement  ({reps} paired reps, ~{window:g}s windows)")
    for case, outcome in zip(case_file.cases, result.per_case):
        comparison = compare_case(
            case_path,
            case.label,
            repeats=outcome.repeats,
            mutates=outcome.mutates_args,
            reps=outcome.reps,
            meter=meter,
        )
        outcome.record(comparison)
        result.note_coverage(meter, comparison.domains, log)
        log(f"  {case.label:<12} {outcome.energy_saved_pct:+7.2f}% energy "
            f"+-{outcome.energy_ci_pct:.2f}%   "
            f"{'significant' if outcome.significant else 'not significant':<15}"
            f"time {outcome.time_saved_pct:+.2f}% +-{outcome.time_ci_pct:.2f}%")

    if canary:
        deciding = result.deciding
        floor = noise_floor(
            case_path, result.deciding_case,
            repeats=deciding.repeats, mutates=deciding.mutates_args,
            reps=deciding.reps, meter=meter,
        )
        result.noise_floor_pct = abs(floor.energy_saved_pct) + floor.energy_ci_pct
        log(f"\nnoise floor  ({result.deciding_case}, before vs before)"
            f"  +-{result.noise_floor_pct:.2f}%")

    _log_scale_note(result, log)
    _decide(result)
    return result


def _log_scale_note(result: Verification, log) -> None:
    """Explain away the losses that look alarming and are not.

    A repair tuned for bulk input often measures far worse on an empty one --
    building a list to join nothing beats returning a constant by a wide
    *ratio* and a negligible *amount*. Printing the ratio without the amount
    invites the reader to reject a good repair, so print both.
    """
    deciding = result.deciding
    if deciding is None or deciding.before_s_per_call <= 0:
        return
    threshold = deciding.before_s_per_call * REGRESSION_TOLERANCE_PCT / 100.0
    negligible = [
        case for case in result.per_case
        if case is not deciding
        and case.significant
        and case.energy_saved_pct < 0
        and 0 < case.excess_s_per_call <= threshold
    ]
    if not negligible:
        return
    log("\nscale note")
    for case in negligible:
        log(f"  {case.label:<12} reads as {case.energy_saved_pct:+.0f}%, but that is "
            f"{_duration(case.excess_s_per_call)}/call against "
            f"{_duration(deciding.before_s_per_call)} on {deciding.label!r}. "
            f"Not disqualifying.")


def _harmful_cases(result: Verification, deciding: CaseOutcome) -> list[CaseOutcome]:
    """Cases the repair measurably hurts.

    A loss has to pass two tests, because there are two different ways for one
    to be an artefact.

    It has to be *large enough to care about*, judged against the deciding
    case's per-call cost rather than its own, so a relative blow-up on a
    microsecond input cannot veto a repair that saves real work on the input
    the code actually sees. See REGRESSION_TOLERANCE_PCT.

    And it has to be *large enough to believe*, which means clearing this
    host's noise floor -- the same bar a saving has to clear. Without the
    symmetry the rig can refuse to call a saving real at 2% and still let a 2%
    loss sink the whole verdict, which is contamination deciding the answer in
    one direction only.
    """
    if deciding.before_s_per_call <= 0:
        return []
    threshold = deciding.before_s_per_call * REGRESSION_TOLERANCE_PCT / 100.0
    return [
        case for case in result.per_case
        if case.significant
        and case.energy_saved_pct < 0
        and case.excess_s_per_call > threshold
        and abs(case.energy_saved_pct) > result.noise_floor_pct
    ]


def _helped_cases(result: Verification) -> list[CaseOutcome]:
    """Cases the repair measurably helps: significant, positive, above floor."""
    return [
        case for case in result.per_case
        if case.significant
        and case.energy_saved_pct > 0
        and case.energy_saved_pct > result.noise_floor_pct
    ]


def _decide(result: Verification) -> None:
    """Apply the verdict rules.

    Five outcomes, and they answer five different questions. The rules below
    are written so that each status means exactly one thing:

        confirmed     every case that moved, moved the right way
        mixed         helps some inputs, hurts others -- a trade-off
        regressed     every case that moved, got worse
        negligible    measured cleanly; nothing moved more than the noise
        inconclusive  this host could not resolve an effect of this size

    The last two are opposite claims and must never be collapsed. `negligible`
    says the repair does nothing on a machine quiet enough to tell. That is
    evidence. `inconclusive` says the machine was too noisy for the question,
    which is a fact about the host and no evidence about the code at all.
    """
    deciding = result.deciding
    if deciding is None:
        result.status = "error"
        result.reason = "no case was measured."
        return

    helped = _helped_cases(result)
    hurt = _harmful_cases(result, deciding)
    floor = result.noise_floor_pct

    if helped and hurt:
        result.status = "mixed"
        result.reason = _mixed_reason(result, helped, hurt)
    elif hurt:
        result.status = "regressed"
        result.reason = _regressed_reason(result, hurt)
    elif helped:
        result.status = "confirmed"
        result.reason = _confirmed_reason(result, helped)
    elif floor > USABLE_FLOOR_PCT:
        result.status = "inconclusive"
        result.reason = (
            f"this host's noise floor measured {floor:.1f}%, above the "
            f"{USABLE_FLOOR_PCT:.1f}% needed to resolve the "
            f"{deciding.energy_saved_pct:+.1f}% seen on {deciding.label!r}. The "
            f"canary compares identical code against itself, so that figure is "
            f"contamination, not the repair. Re-run on an idle machine before "
            f"concluding anything; this is not evidence either way."
        )
    else:
        result.status = "negligible"
        biggest = max(result.per_case, key=lambda c: abs(c.energy_saved_pct))
        result.reason = (
            f"no case moved more than the noise: the largest reading was "
            f"{biggest.energy_saved_pct:+.1f}% +-{biggest.energy_ci_pct:.1f}% on "
            f"{biggest.label!r}, against a clean {floor:.1f}% floor across "
            f"{len(result.per_case)} cases. The pattern is here and removing it "
            f"saves nothing measurable, so it is not worth repairing in this "
            f"code."
        )


def _confirmed_reason(result: Verification, helped: list[CaseOutcome]) -> str:
    best = max(helped, key=lambda c: c.energy_saved_pct)
    labels = ", ".join(repr(c.label) for c in helped)
    reason = (
        f"{best.energy_saved_pct:.1f}% +-{best.energy_ci_pct:.1f}% energy saved "
        f"on {best.label!r}, clearing the {result.noise_floor_pct:.1f}% noise "
        f"floor. Improved on {len(helped)} of {len(result.per_case)} cases "
        f"({labels}) and measurably worse on none, with behaviour preserved "
        f"throughout."
    )
    if result.relaxations:
        # A confirmed verdict on a weakened check has to carry that with it,
        # or the weakening disappears the moment the number is quoted.
        reason += (
            " Behaviour was compared under a relaxed rule, which the report "
            "must repeat: " + "; ".join(result.relaxations) + "."
        )
    if best.energy_only:
        reason += (
            " Energy improved while wall-clock time did not -- an "
            "energy-specific effect worth calling out in the report."
        )
    return reason


def _mixed_reason(
    result: Verification, helped: list[CaseOutcome], hurt: list[CaseOutcome]
) -> str:
    """A trade-off: real on both sides, so the report needs both named."""
    best = max(helped, key=lambda c: c.energy_saved_pct)
    worst = max(hurt, key=lambda c: c.excess_s_per_call)
    return (
        f"a trade-off, not a fix: {best.energy_saved_pct:.1f}% saved on "
        f"{best.label!r} but {abs(worst.energy_saved_pct):.1f}% lost on "
        f"{worst.label!r}, both clearing the {result.noise_floor_pct:.1f}% "
        f"noise floor. Whether it pays depends on which input the code actually "
        f"sees, so the card must name both cases and let the agent judge."
    )


def _regressed_reason(result: Verification, hurt: list[CaseOutcome]) -> str:
    """Worse everywhere it measurably moved."""
    worst = max(hurt, key=lambda c: c.excess_s_per_call)
    labels = ", ".join(repr(c.label) for c in hurt)
    return (
        f"the repair costs more than the code it replaces: "
        f"{abs(worst.energy_saved_pct):.1f}% lost on {worst.label!r}, above the "
        f"{result.noise_floor_pct:.1f}% noise floor, and no case improved. "
        f"Worse on {len(hurt)} of {len(result.per_case)} cases ({labels})."
    )


def _duration(seconds: float) -> str:
    """Human-scaled timing, so a microsecond case is obviously a microsecond case."""
    for threshold, unit, scale in ((1e-3, "us", 1e6), (1.0, "ms", 1e3)):
        if seconds < threshold:
            return f"{seconds * scale:.1f} {unit}"
    return f"{seconds:.3f} s"


def _size(before_spc: float, after_spc: float, window: float,
          reps: int) -> tuple[int, int, bool]:
    """Repeat count, repetitions, and whether the slow side forced a clamp.

    Both variants run the same number of calls -- that is what makes the
    comparison fair -- so there is one count to choose, and it is chosen from
    the *faster* variant. The faster one is the only side at risk of a window
    too short to resolve; the slower one is already over-resolved by being
    slow, and giving it a full window on its own terms would mean comparing
    different amounts of work.

    See SLOW_WINDOW_BUDGET_S for why clamping the result is safe.
    """
    fast = min(before_spc, after_spc)
    slow = max(before_spc, after_spc)

    wanted = choose_repeats(fast, window)
    if slow <= 0:
        return wanted, reps, False

    affordable = max(1, int(SLOW_WINDOW_BUDGET_S / slow))
    if wanted <= affordable:
        return wanted, reps, False

    # One call of the slow side already costs more than the whole budget, so
    # there is nothing left to trim from the count. Trim the repetitions
    # instead: the effect that makes a case this lopsided is not one a wider
    # interval will hide.
    if affordable <= 1 and slow > SLOW_WINDOW_BUDGET_S:
        return 1, min(reps, REDUCED_REPS), True
    return affordable, reps, True


def _time_one_call(case_file: CaseFile, case: Case, variant=None) -> float:
    """Seconds per call of one variant, used only to size the measured window."""
    function = variant if variant is not None else case_file.before
    timings = []
    for _ in range(TIMING_CALLS):
        args = case.args()
        start = time.perf_counter()
        function(*args)
        timings.append(time.perf_counter() - start)
    # Median, not minimum. The fastest of several calls is the one that met the
    # warmest cache and the least interference, which is not the rate the
    # measured loop will sustain. Sizing from it underestimates the per-call
    # cost and so overestimates how many calls fit in a window, which is how a
    # window sized for 3s ends up running for fifteen.
    return statistics.median(timings)


# -- entry point -----------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("case_file", type=Path, nargs="?",
                        help="a file defining before(), after() and cases()")
    parser.add_argument("--calibrate", action="store_true",
                        help="measure this host's noise floor and stop")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument("--window", type=float, default=TARGET_WINDOW_S,
                        help="target seconds per measured window (default 3)")
    parser.add_argument("--meter", default="auto")
    parser.add_argument("--no-canary", action="store_true",
                        help="skip the null canary (faster, and less trustworthy)")
    args = parser.parse_args(argv)

    if args.calibrate and args.case_file is None:
        return _calibrate(args)
    if args.case_file is None:
        parser.error("give a case file, or --calibrate")

    log = (lambda *a, **k: None) if args.json else print
    try:
        result = verify(
            args.case_file,
            reps=args.reps,
            meter=args.meter,
            window=args.window,
            canary=not args.no_canary,
            log=log,
        )
    except (CaseFileError, MeasurementError) as exc:
        if args.json:
            json.dump({"status": "error", "reason": str(exc)}, sys.stdout, indent=1)
            print()
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(result.to_dict(), sys.stdout, indent=1)
        print()
    else:
        print(f"\nVERDICT: {result.status}")
        print(f"  {result.reason}")

    return 0 if result.status == "confirmed" else 1


def _calibrate(args) -> int:
    """Measure the host's resolution limit on a known, stable workload."""
    if not args.json:
        print(f"calibrating on {CANARY_CASE.name}: identical code, measured "
              f"against itself.\nThe answer must come back insignificant.\n")
    case_file = load_case_file(CANARY_CASE)
    case = case_file.cases[-1]
    seconds = _time_one_call(case_file, case)
    repeats = choose_repeats(seconds, args.window)

    floor = noise_floor(CANARY_CASE, case.label, repeats=repeats,
                        reps=args.reps, meter=args.meter)
    limit = abs(floor.energy_saved_pct) + floor.energy_ci_pct
    payload = {
        "noise_floor_pct": round(limit, 2),
        "apparent_saving_pct": round(floor.energy_saved_pct, 2),
        "ci_pct": round(floor.energy_ci_pct, 2),
        "baseline_energy_j": round(floor.baseline_energy_j, 3),
        "usable": not floor.energy_significant,
    }
    if args.json:
        json.dump(payload, sys.stdout, indent=1)
        print()
        return 0 if payload["usable"] else 1

    print(f"  baseline        {floor.baseline_energy_j:.2f} J per window")
    print(f"  apparent saving {floor.energy_saved_pct:+.2f}% "
          f"+-{floor.energy_ci_pct:.2f}%")
    if floor.energy_significant:
        print("\nFAIL: identical code measured as different. Something else is "
              "running on this host.\nNothing measured right now means anything.")
        return 1
    print(f"\nOK. This host resolves about {limit:.1f}%. Require real effects to "
          f"clear that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
