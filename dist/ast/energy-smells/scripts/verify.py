#!/usr/bin/env python3
"""Prove a repair saves energy, or find out that it does not.

    python verify.py cases/my_case.py            readable report
    python verify.py cases/my_case.py --json     for findings.json
    python verify.py --calibrate                    this host's noise floor

A case file supplies `before`, `after` and `cases()`; see reference/verifying.md
for the contract. This script then does four things, in order:

    1. equivalence   `after` must behave exactly like `before` on every case
    2. sizing        each case is repeated until its window lasts ~2 seconds
    3. measurement   the two variants alternate inside one process, 7 paired reps
    4. the canary    `before` against itself, to bound what this host can resolve

The verdict is the point. `confirmed` means a real, measured, behaviour-
preserving saving. `refuted` means the repair was built and measured and did
nothing -- which is not a failure of the analysis, it is the analysis working.
"""

from __future__ import annotations

import argparse
import json
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
from lib.models import Comparison  # noqa: E402

CANARY_CASE = Path(__file__).resolve().parent / "lib" / "canary_case.py"

REGRESSION_TOLERANCE_PCT = 1.0
"""When a loss on one case is big enough to sink an otherwise good repair.

Measured as a percentage of the *deciding* case's per-call cost, not of the
case's own. That distinction is the whole rule. Joining an empty list costs
1.3 microseconds where returning `""` costs 0.4, so on an empty case the repair
measures as three times worse -- a true statement about a quantity nobody
cares about. Weighted against a deciding case that takes 8.7 milliseconds, the
same loss is 0.01% and correctly ignored.

A repair that costs 20% on a case a tenth the size of the deciding one is a
different matter: that is 2% of real work, it clears this bar, and the verdict
calls it a trade-off.

This is one of two bars. The loss must also clear the host's noise floor, for
the same reason a saving must. See `_worst_regression`.
"""

TIMING_CALLS = 3
"""Calls used to estimate per-call cost. Enough to avoid a cold-start outlier."""

USABLE_FLOOR_PCT = 3.0
"""Above this canary reading, a null result means nothing and says so.

An idle host measures about 0.6%. Three percent leaves headroom for ordinary
background activity while still catching a machine that has become unusable --
which is not hypothetical: a single concurrent user moved the median canary to
8.2% and one reading to 51%, and every "the repair saves nothing" verdict in
that band was an artefact of the host rather than a fact about the code.
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
    repeats: int = 0
    energy_saved_pct: float = 0.0
    energy_ci_pct: float = 0.0
    time_saved_pct: float = 0.0
    time_ci_pct: float = 0.0
    significant: bool = False
    energy_only: bool = False
    baseline_energy_j: float = 0.0
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
    status: str = "refuted"
    reason: str = ""
    deciding_case: str = ""
    noise_floor_pct: float = 0.0
    reps: int = DEFAULT_REPS
    per_case: list[CaseOutcome] = field(default_factory=list)
    relaxations: tuple[str, ...] = ()
    """Ways this case file weakened the equivalence check, if any."""

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
            "per_case": [
                {
                    "label": case.label,
                    "repeats": case.repeats,
                    "energy_saved_pct": round(case.energy_saved_pct, 2),
                    "energy_ci_pct": round(case.energy_ci_pct, 2),
                    "significant": case.significant,
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
        outcome.seconds_per_call = _time_one_call(case_file, case)
        outcome.repeats = choose_repeats(outcome.seconds_per_call, window)
        log(f"  {case.label:<12} {_duration(outcome.seconds_per_call):>10}/call"
            f"  ->  {outcome.repeats:,} repeats")

    result.deciding_case = max(result.per_case, key=lambda c: c.seconds_per_call).label

    log(f"\nmeasurement  ({reps} paired reps, ~{window:g}s windows)")
    for case, outcome in zip(case_file.cases, result.per_case):
        comparison = compare_case(
            case_path,
            case.label,
            repeats=outcome.repeats,
            mutates=outcome.mutates_args,
            reps=reps,
            meter=meter,
        )
        outcome.record(comparison)
        log(f"  {case.label:<12} {outcome.energy_saved_pct:+7.2f}% energy "
            f"+-{outcome.energy_ci_pct:.2f}%   "
            f"{'significant' if outcome.significant else 'not significant':<15}"
            f"time {outcome.time_saved_pct:+.2f}% +-{outcome.time_ci_pct:.2f}%")

    if canary:
        deciding = result.deciding
        floor = noise_floor(
            case_path, result.deciding_case,
            repeats=deciding.repeats, mutates=deciding.mutates_args,
            reps=reps, meter=meter,
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


def _decide(result: Verification) -> None:
    """Apply the verdict rules. All of them, in priority order."""
    deciding = result.deciding
    if deciding is None:
        result.status = "refuted"
        result.reason = "no case was measured."
        return

    worst = _worst_regression(result, deciding)
    if worst is not None:
        result.status = "regressed"
        result.reason = _regression_reason(result, deciding, worst)
        return

    clears_floor = deciding.energy_saved_pct > result.noise_floor_pct
    if deciding.significant and deciding.energy_saved_pct > 0 and clears_floor:
        result.status = "confirmed"
        result.reason = (
            f"{deciding.energy_saved_pct:.1f}% +-{deciding.energy_ci_pct:.1f}% "
            f"energy saved on {deciding.label!r}, clearing the "
            f"{result.noise_floor_pct:.1f}% noise floor, with behaviour preserved "
            f"on all {len(result.per_case)} cases."
        )
        if result.relaxations:
            # A confirmed verdict on a weakened check has to carry that with it,
            # or the weakening disappears the moment the number is quoted.
            result.reason += (
                " Behaviour was compared under a relaxed rule, which the report "
                "must repeat: " + "; ".join(result.relaxations) + "."
            )
        if deciding.energy_only:
            result.reason += (
                " Energy improved while wall-clock time did not -- an "
                "energy-specific effect worth calling out in the report."
            )
        return

    # Below here the repair did not clear the bar. *Why* it did not decides the
    # verdict, and the two reasons are opposite claims about the world:
    #
    #   refuted       we measured cleanly and the repair does nothing
    #   inconclusive  this host could not resolve an effect of this size
    #
    # Collapsing them into `refuted` is how a busy machine gets recorded as
    # evidence against the repair. On an idle host the canary reads about
    # 0.6%; sharing the machine with one other user pushed the median to 8.2%
    # and one run to 51%, at which point nothing under half is measurable and
    # "saves nothing" is not a claim the data supports.
    if result.noise_floor_pct > USABLE_FLOOR_PCT:
        result.status = "inconclusive"
        result.reason = (
            f"this host's noise floor measured {result.noise_floor_pct:.1f}%, "
            f"above the {USABLE_FLOOR_PCT:.1f}% needed to resolve the "
            f"{deciding.energy_saved_pct:+.1f}% seen on {deciding.label!r}. The "
            f"canary compares identical code against itself, so that figure is "
            f"contamination, not the repair. Re-run on an idle machine before "
            f"concluding anything; do not report this candidate either way."
        )
        return

    result.status = "refuted"
    if not deciding.significant:
        result.reason = (
            f"no significant change on {deciding.label!r} "
            f"({deciding.energy_saved_pct:+.1f}% +-{deciding.energy_ci_pct:.1f}%) "
            f"against a clean {result.noise_floor_pct:.1f}% noise floor. The "
            f"pattern is there; removing it saves nothing measurable, so it is "
            f"not worth repairing in this code."
        )
    elif not clears_floor:
        result.reason = (
            f"the {deciding.energy_saved_pct:+.1f}% saving on {deciding.label!r} "
            f"does not clear this host's {result.noise_floor_pct:.1f}% noise "
            f"floor. Scale the largest case up and re-run, or report as refuted."
        )
    else:
        result.reason = (
            f"the repair saves nothing: {deciding.energy_saved_pct:+.1f}% on "
            f"{deciding.label!r}."
        )


def _regression_reason(
    result: Verification, deciding: CaseOutcome, worst: CaseOutcome
) -> str:
    """Say what actually happened, rather than what usually happens.

    This used to be one fixed sentence: "the repair helps the large case but
    costs N% on X". Both halves were claims the verdict had never checked. The
    deciding case is whichever costs most per call and is named by the case
    file, so it is only called "large" by coincidence -- and in most regressions
    it is precisely the case the repair made worse, which makes "the repair
    helps" it exactly backwards.

    Three situations hide behind one verdict, and the report needs them apart:
    a genuine trade-off, a repair that helps some input but not the one that
    dominates the cost, and a repair that is worse everywhere it was measured.
    """
    gained = [c.label for c in result.per_case
              if c.significant and c.energy_saved_pct > 0]

    if worst is deciding:
        # The share-of-deciding-cost figure exists to say "this loss is real
        # work, not a ratio on a microsecond input". It says nothing when the
        # case that lost is the one being compared against.
        loss = f"{abs(worst.energy_saved_pct):.1f}% lost on it"
        elsewhere = ""
    else:
        cost = 100.0 * worst.excess_s_per_call / deciding.before_s_per_call
        loss = (f"{abs(worst.energy_saved_pct):.1f}% lost on {worst.label!r}, "
                f"worth {cost:.1f}% of {deciding.label!r}'s own per-call cost, "
                f"so it is real work and not rounding")
        elsewhere = f" and {loss}"

    if deciding.significant and deciding.energy_saved_pct > 0:
        return (
            f"a trade-off rather than a fix: {deciding.energy_saved_pct:.1f}% "
            f"saved on {deciding.label!r}, the case that dominates the cost, "
            f"against {loss}. Report under `refuted` and name both cases."
        )
    if gained:
        helped = ", ".join(repr(label) for label in gained)
        return (
            f"the repair helps {helped}, but not {deciding.label!r}, the case "
            f"that dominates the cost, which read "
            f"{deciding.energy_saved_pct:+.1f}%{elsewhere}. Report under "
            f"`refuted` and say which inputs it is for."
        )
    return (
        f"no case improved: {deciding.label!r}, the case that dominates the "
        f"cost, read {deciding.energy_saved_pct:+.1f}%{elsewhere}. The repair "
        f"costs more than the code it replaces on every input measured; report "
        f"under `refuted`."
    )


def _worst_regression(result: Verification, deciding: CaseOutcome) -> CaseOutcome | None:
    """The case the repair hurts most, if any loss is big enough to matter.

    A loss has to pass two tests, because there are two different ways for one
    to be an artefact.

    It has to be *large enough to care about*, judged against the deciding
    case's per-call cost rather than its own, so a relative blow-up on a
    microsecond input cannot veto a repair that saves real work on the input
    the code actually sees. See the tolerance constant.

    And it has to be *large enough to believe*, which means clearing this
    host's noise floor -- the same bar a saving has to clear to be confirmed.
    Without the symmetry the rig can refuse to call a saving real at 2% and
    still let a 2% loss on another case sink the whole verdict, which is the
    contamination deciding the answer in one direction only.
    """
    if deciding.before_s_per_call <= 0:
        return None
    threshold = deciding.before_s_per_call * REGRESSION_TOLERANCE_PCT / 100.0
    harmful = [
        case for case in result.per_case
        if case.significant
        and case.energy_saved_pct < 0
        and case.excess_s_per_call > threshold
        and abs(case.energy_saved_pct) > result.noise_floor_pct
    ]
    return max(harmful, key=lambda c: c.excess_s_per_call, default=None)


def _duration(seconds: float) -> str:
    """Human-scaled timing, so a microsecond case is obviously a microsecond case."""
    for threshold, unit, scale in ((1e-3, "us", 1e6), (1.0, "ms", 1e3)):
        if seconds < threshold:
            return f"{seconds * scale:.1f} {unit}"
    return f"{seconds:.3f} s"


def _time_one_call(case_file: CaseFile, case: Case) -> float:
    """Seconds per call of `before`, used only to size the measured window."""
    best = float("inf")
    for _ in range(TIMING_CALLS):
        args = case.args()
        start = time.perf_counter()
        case_file.before(*args)
        best = min(best, time.perf_counter() - start)
    return best


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
                        help="target seconds per measured window (default 2)")
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
