#!/usr/bin/env python3
"""Prove a repair saves energy, or find out that it does not.

    python verify.py submissions.jsonl --repo .     every repair in the file
    python verify.py --calibrate                     this host's noise floor
    python verify.py case.py                         one of our validation files

A submission names a unit in a repository and gives the replacement source and
the inputs; `before` is read from the repository itself. A pristine copy and a
patched copy are imported side by side in one worker process, each under its
real package names, and measured alternately, one window at a time. A case
file defines `before`, `after` and `cases()` itself; it is how our own
validation samples are written.

Either way the same four stages decide the result:

    1. equivalence   the repair must behave exactly like the original
    2. sizing        each case is repeated until its window lasts long enough
    3. measurement   the two variants alternate, paired repetition by repetition
    4. noise floor   identical code against itself, to bound what the host resolves

The verdict is the point, and there are five of them:

    confirmed     every case that moved, moved the right way
    mixed         helps some inputs, hurts others -- a trade-off
    regressed     every case that moved, got worse
    negligible    measured cleanly; nothing moved more than the noise
    inconclusive  this host could not resolve an effect of this size

and three for when nothing was measured: `not_equivalent` (the repair is
broken), `invalid` (the submission is malformed) and `error` (the environment
failed -- an import, a meter, a library the unit needs and the host lacks).

`negligible` is the analysis working, not failing: the repair was built and
measured and does nothing. `inconclusive` is the opposite -- it says nothing
about the code, only that the machine was too noisy to ask. Collapsing those
two is how a busy host gets recorded as evidence against a repair.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import equivalence  # noqa: E402
from lib import meters  # noqa: E402
from lib.casefile import RELAXATIONS, Case, CaseFile, CaseFileError, load_case_file  # noqa: E402
from lib.measure import (  # noqa: E402
    DEFAULT_REPS,
    MeasurementError,
    _summarise,
    choose_repeats,
    compare_case,
    noise_floor,
)
from lib.models import Comparison  # noqa: E402
from lib.pair import LoadError, Pair, WorkerError, stage  # noqa: E402
from lib.submission import (  # noqa: E402
    case_count_problem,
    submission_hash,
    validate,
    validate_file,
)

CANARY_CASE = Path(__file__).resolve().parent / "lib" / "canary_case.py"


@dataclass(frozen=True)
class Profile:
    """How long and how often to measure. Two exist, for two different jobs."""

    name: str
    window: float
    """Target seconds per measured window, on the faster variant."""
    reps: int
    """Paired repetitions per case."""
    canary: bool
    """Measure the noise floor on this run's own largest case. Without it the
    floor comes from the session's calibration."""
    warmup: float
    """Seconds of unrelated arithmetic before the first window, so the machine
    is at a steady clock before anything is charged to either variant."""
    slow_factor: float
    """Ceiling on the slower variant's window, as a multiple of `window`. See
    `_size` for why clamping there is safe."""


PROFILES = {
    # Every submitted repair, by the agent and when we re-measure: about a
    # minute each. On the development host two copies of identical code read
    # within about 1% per case with these settings, and the session floor (ten
    # repetitions) came out at 1-3%.
    "fast": Profile("fast", window=1.0, reps=5, canary=False, warmup=3.0, slow_factor=2.0),
    # Our validation case files only, unchanged since the first measured run,
    # so the 230 recorded results stay comparable with anything re-run.
    "validation": Profile("validation", window=3.0, reps=9, canary=True, warmup=10.0,
                          slow_factor=5.0),
}

FINAL = {"confirmed", "mixed", "regressed", "negligible"}
"""A measured result. The line that produced it may not be edited afterwards:
re-measuring an edited line would replace the result, and a repair could then
be reshaped until it confirmed with nothing on record. A genuinely different
repair is a new line, listed in `related`."""

REMEASURED = {"inconclusive", "error"}
"""Not a result about the repair -- a busy host, a failed environment -- so the
next run measures the line again without it having to change."""

TIMING_CALLS = 5
"""Calls used to estimate per-call cost. Enough to avoid a cold-start outlier."""

REDUCED_REPS = 3
"""Paired repetitions used when a single call already exceeds the budget.

At that point the effect is far past anything a confidence interval needs to
separate from zero, and nine repetitions of a window that cannot be shortened
is most of an hour for one case."""

USABLE_FLOOR_PCT = 3.0
"""Above this noise floor, a null result means nothing and says so.

This is a policy bar, not a property of any particular machine: it is the point
past which "the repair saves nothing" stops being a claim the data supports,
because effects smaller than the host's own noise cannot be distinguished from
zero. A quiet host sits far below it; a host with another user on it can sit an
order of magnitude above, and every null verdict measured in that band is an
artefact of the machine rather than a fact about the code.

The floor itself is never assumed. Validation case files measure it on every
run with the canary; submitted repairs use the session's calibration
(`--calibrate`, taken automatically when none is fresh). When moving to a new machine, calibrate first: if its quiet floor
is not comfortably under this bar, the problem is the host, not the threshold,
and raising the threshold only hides it.
"""

CALIBRATION_REPS = 10
"""Paired repetitions for the session calibration, whatever the profile.

The floor bounds what identical code reads on this host -- contamination, not
the sampling noise of estimating it. With five repetitions the estimate's own
interval (t = 2.78 over root five) made up most of the floor, so it came out at
3-5% on a host whose identical-code readings sat within one percent. Calibration
runs once per session, so it can afford ten; an even number also puts each side
first equally often."""

CALIBRATION_TTL_S = 3 * 3600
"""How long a calibration is trusted. Long enough for a session, short enough
that a floor measured on a quiet morning is not applied to a busy afternoon."""


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
    """Reported, never decided on. Kept so a reader can see when energy and
    duration diverge; no verdict rule reads either field."""
    significant: bool = False
    baseline_energy_j: float = 0.0
    baseline_power_w: float = 0.0
    patched_power_w: float = 0.0
    before_s_per_call: float = 0.0
    after_s_per_call: float = 0.0
    before_energy_j: float = 0.0
    after_energy_j: float = 0.0
    """Mean joules per measured window. Every verdict rule is written against
    these and nothing else: not time, not power."""

    def record(self, comparison: Comparison) -> None:
        self.energy_saved_pct = comparison.energy_saved_pct
        self.energy_ci_pct = comparison.energy_ci_pct
        self.time_saved_pct = comparison.time_saved_pct
        self.time_ci_pct = comparison.time_ci_pct
        self.significant = comparison.energy_significant
        self.baseline_energy_j = comparison.baseline_energy_j
        self.baseline_power_w = comparison.baseline_power_w
        self.patched_power_w = comparison.patched_power_w
        self.baseline_window_s = comparison.baseline_duration_s
        self.patched_window_s = comparison.patched_duration_s
        self.before_s_per_call = comparison.baseline_duration_s / self.repeats
        self.after_s_per_call = comparison.patched_duration_s / self.repeats
        self.before_energy_j = comparison.baseline_energy_j
        self.after_energy_j = comparison.patched_energy_j

    @property
    def before_energy_per_call(self) -> float:
        return self.before_energy_j / self.repeats if self.repeats else 0.0

    @property
    def excess_energy_per_call(self) -> float:
        """Extra joules `after` costs per call. Negative when the repair helps.

        This is the quantity a regression is judged on. It used to be the time
        equivalent, which meant a verdict about energy could turn on a
        stopwatch."""
        if not self.repeats:
            return 0.0
        return (self.after_energy_j - self.before_energy_j) / self.repeats


@dataclass
class Verification:
    """The verdict, and everything it was derived from."""

    case_file: str
    """What was measured: a case file's path, or a submission's id."""
    status: str = "negligible"
    reason: str = ""
    canary_case: str = ""
    """Which case the noise floor was measured on. Provenance for that one
    number, not a headline: the floor has to be measured on something, and
    measuring it on every case would roughly double the batch."""
    noise_floor_pct: float = 0.0
    reps: int = DEFAULT_REPS
    per_case: list[CaseOutcome] = field(default_factory=list)
    relaxations: tuple[str, ...] = ()
    """Ways this case file weakened the equivalence check, if any."""
    coverage: dict = field(default_factory=dict)
    """Which meter took the readings and which energy domains it could see."""
    profile: str = "fast"
    """Which measurement profile ran; see PROFILES."""
    floor_source: str = ""
    """Where `noise_floor_pct` came from: this run's canary, or the session's
    calibration."""
    stubbed: tuple[str, ...] = ()
    """Uninstalled packages stood in for while loading the unit, if any."""

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
    def canary(self) -> CaseOutcome | None:
        return next((c for c in self.per_case if c.label == self.canary_case), None)

    def to_dict(self) -> dict:
        """The row written to results/<suite>.jsonl.

        What is reported is what was measured: joules and seconds for each
        variant, on each case. Percentages of energy saved are not stored --
        they are a view of the same two numbers, and storing a derived figure
        beside its inputs invites the two to disagree.

        `energy_ci_pct` is the exception and is not a saving. It is the
        half-width of the 95% interval on the paired per-repetition
        comparison, which is the only thing here that cannot be recovered from
        the means, and without it `significant` cannot be judged.

        There is no headline case. `status` says whether every case improved,
        some did, or none did, and `per_case` carries what each one measured.
        Promoting one case's numbers to the top of the row only invited them to
        be quoted as though they were the file's result.
        """
        return {
            "status": self.status,
            "reason": self.reason,
            "case_file": self.case_file,
            "profile": self.profile,
            "cases_checked": len(self.per_case),
            "noise_floor_pct": round(self.noise_floor_pct, 2),
            "noise_floor_from": self.floor_source,
            "canary_case": self.canary_case,
            "reps": self.reps,
            "equivalence_relaxed": list(self.relaxations),
            "stubbed": list(self.stubbed),
            "coverage": self.coverage,
            "per_case": [
                {
                    "label": case.label,
                    "repeats": case.repeats,
                    "reps": case.reps,
                    "clamped": case.clamped,
                    "before_energy_j": round(case.before_energy_j, 4),
                    "after_energy_j": round(case.after_energy_j, 4),
                    "before_time_s": round(case.baseline_window_s, 4),
                    "after_time_s": round(case.patched_window_s, 4),
                    "before_power_w": round(case.baseline_power_w, 2),
                    "after_power_w": round(case.patched_power_w, 2),
                    "before_s_per_call": case.before_spc,
                    "after_s_per_call": case.after_spc,
                    "energy_ci_pct": round(case.energy_ci_pct, 2),
                    "significant": case.significant,
                }
                for case in self.per_case
            ],
        }


# -- engines ---------------------------------------------------------------
#
# The pipeline below is written once, against these two. Each one answers the
# same five questions -- what are the cases, do the variants agree, how long
# does one call take, what does a measured pair read, what does identical code
# read -- for its own kind of input.


@dataclass
class CheckRow:
    """The equivalence check on one input."""

    label: str
    measured: bool
    """True for one of the measured cases; False for an equivalence-only check."""
    difference: str = ""
    mutates: bool = False


class CaseFileEngine:
    """One of our validation files: `before`, `after` and `cases()` in one module.

    Both variants run inside one interpreter, in a child process per case
    (`lib/_runner.py`), which also does its own machine warm-up.
    """

    subject_key = "case_file"

    def __init__(self, path: Path):
        self.path = Path(path)
        self.case_file = load_case_file(self.path)
        self.subject = str(path)
        self.labels = [case.label for case in self.case_file.cases]
        self.relaxations = self.case_file.relaxations
        self.stubbed: tuple[str, ...] = ()

    def check(self) -> list[CheckRow]:
        rows = []
        for case in self.case_file.cases:
            checked = equivalence.check(self.case_file, case)
            rows.append(CheckRow(case.label, True, checked.difference, checked.mutates_args))
        return rows

    def time(self, index: int, side: str) -> float:
        return _time_one_call(self.case_file, self.case_file.cases[index], side)

    def warm(self, seconds: float) -> None:
        """Nothing to do here: the runner warms the machine for every case."""

    def measure(self, plans: list[dict], *, meter: str) -> list[Comparison]:
        """One child process per case, both variants alternating inside it."""
        return [compare_case(self.path, self.labels[p["index"]], repeats=p["repeats"],
                             mutates=p["mutates"], reps=p["reps"], meter=meter)
                for p in plans]

    def floor(self, plan: dict, *, meter: str) -> Comparison:
        return noise_floor(self.path, self.labels[plan["index"]], repeats=plan["repeats"],
                           mutates=plan["mutates"], reps=plan["reps"], meter=meter)

    def close(self) -> None:
        pass


class SubmissionError(ValueError):
    """The submission cannot be run as written. The message says why."""


class PairEngine:
    """A submitted repair: two copies of the repository, side by side in one worker."""

    subject_key = "id"

    def __init__(self, repo: Path, record: dict, work: Path, *, meter: str,
                 require_counts: bool = True):
        self.record = record
        self.work = Path(work)
        self.subject = record.get("id", "?")
        self.meter = meter
        try:
            self.before_root, self.after_root = stage(Path(repo), record["changed"], self.work)
        except (KeyError, FileNotFoundError, SyntaxError, ValueError) as exc:
            raise SubmissionError(f"could not apply `changed`: {type(exc).__name__}: {exc}")
        try:
            self.pair = Pair(self.before_root, self.after_root, record["unit"],
                             record["cases_source"], self.work, meter)
        except LoadError as exc:
            if exc.stage == "import" and exc.side == "before":
                raise MeasurementError(
                    f"the repository's own module does not import here: {exc}. "
                    f"Run from the environment the repository builds in."
                ) from exc
            if exc.stage == "import":
                raise SubmissionError(f"the patched module does not import: {exc}") from exc
            if exc.stage == "cases":
                raise SubmissionError(f"`cases_source` failed: {exc}") from exc
            raise MeasurementError(f"{exc.side} side failed to start: {exc}") from exc

        if require_counts:
            problem = case_count_problem(self.pair.labels, self.pair.check_labels)
            if problem:
                self.pair.close()
                raise SubmissionError(problem)
        self.labels = self.pair.labels
        self.stubbed = tuple(self.pair.stubbed)
        self.has_equivalent = self.pair.side("before").ready["has_equivalent"]
        if self.has_equivalent and not self.pair.side("before").ready["equivalent_doc"]:
            self.pair.close()
            raise SubmissionError(
                "`equivalent()` needs a docstring saying what it treats as the same "
                "answer. A comparison that always returns True would turn a broken "
                "repair into a confirmed one with nothing in the output to show it."
            )
        self.strict = record.get("equivalence", "strict") == "strict"
        self.relaxations = self._relaxations()

    def _relaxations(self) -> tuple[str, ...]:
        notes = []
        if RELAXATIONS.get(self.record.get("equivalence", "strict")):
            notes.append(RELAXATIONS[self.record["equivalence"]])
        if self.has_equivalent:
            doc = self.pair.side("before").ready["equivalent_doc"].splitlines()[0]
            notes.append(f"return values compared by the submission's own `equivalent()`: {doc}")
        if self.stubbed:
            notes.append("loaded with these uninstalled packages stood in for: "
                         + ", ".join(self.stubbed))
        return tuple(notes)

    def check(self) -> list[CheckRow]:
        rows = []
        for set_name in ("checks", "cases"):
            labels = self.pair.check_labels if set_name == "checks" else self.labels
            for index, label in enumerate(labels):
                a = self.pair.side("before").ask(op="check", set=set_name, index=index,
                                         plain=self.has_equivalent)
                b = self.pair.side("after").ask(op="check", set=set_name, index=index,
                                        plain=self.has_equivalent)
                rows.append(CheckRow(label, set_name == "cases", self._differ(a, b),
                                     a["mutates"] or b["mutates"]))
        return rows

    def _differ(self, a: dict, b: dict) -> str:
        """Which observable channel diverged, in words; empty when none did."""
        if a["kind"] != b["kind"]:
            return f"before {_said(a)}, after {_said(b)}"
        if a["kind"] == "raise":
            return "" if a["raised"] == b["raised"] else \
                f"before raised {a['raised']}, after raised {b['raised']}"
        if self.has_equivalent:
            same = self.pair.side("before").ask(op="equivalent", before=a["plain"],
                                        after=b["plain"])["same"]
            if not same:
                return (f"`equivalent()` says the results differ: before -> "
                        f"{_short(a['value'])}, after -> {_short(b['value'])}")
        elif a["value"] != b["value"]:
            return (f"different return value: before -> {_short(a['value'])}, "
                    f"after -> {_short(b['value'])}")
        if self.strict:
            # The effect of the call on its arguments, not their insides. When
            # the repair changed a constructor the unit's arguments are built
            # differently on the two sides before the call is ever made -- an
            # object holding a set instead of a list -- and that is the repair,
            # not a side effect of the call.
            hint = ("If that is deliberate and no call site depends on the "
                    "mutation, set `\"equivalence\": \"returns_only\"` and give the reason.")
            if a["mutates"] != b["mutates"]:
                return (f"the original {'mutates' if a['mutates'] else 'does not mutate'} "
                        f"its arguments and the repair "
                        f"{'does' if b['mutates'] else 'does not'}. {hint}")
            if a["mutates"] and a["args_before"] == b["args_before"] and a["args"] != b["args"]:
                return f"both versions mutate their arguments, but leave them differently. {hint}"
        if a["stdout"] != b["stdout"]:
            return f"different stdout: {_short(a['stdout'])} vs {_short(b['stdout'])}"
        return ""

    def time(self, index: int, side: str) -> float:
        return self.pair.side(side).ask(op="time", index=index, calls=TIMING_CALLS)["seconds"]

    def warm(self, seconds: float) -> None:
        self.pair.ask(op="warm", seconds=seconds)

    def measure(self, plans: list[dict], *, meter: str) -> list[Comparison]:
        return _alternate(self.pair, plans)

    def close(self) -> None:
        self.pair.close()


def _alternate(pair: Pair, plans: list[dict]) -> list[Comparison]:
    """Paired windows, the two sides taking turns, the order flipped every repetition.

    Both sides live in one process and run on one thread, so the pair shares a
    core, a clock and an address space, and each pair of windows is taken back
    to back. That is what the measurement rests on; `_pair_worker.py` records
    what happened when the two sides were given a process each.
    """
    samples: dict[int, list[dict]] = {i: [] for i in range(len(plans))}
    for slot, plan in enumerate(plans):
        for rep in range(plan["reps"]):
            order = ("before", "after") if rep % 2 == 0 else ("after", "before")
            for name in order:
                reading = pair.side(name).ask(op="window", index=plan["index"],
                                              repeats=plan["repeats"],
                                              mutates=plan["mutates"], warmup_calls=1)
                samples[slot].append({"label": name, "rep": rep, **{
                    key: reading[key] for key in ("energy_j", "duration_s", "power_w", "domains")
                }})
    return [_summarise(samples[slot], reps=plan["reps"]) for slot, plan in enumerate(plans)]


def _said(row: dict) -> str:
    return f"raised {row['raised']}" if row["kind"] == "raise" else f"returned {_short(row['value'])}"


def _short(text: str, limit: int = 120) -> str:
    return text if len(text) <= limit else text[:limit] + "..."


# -- the pipeline ----------------------------------------------------------


def verify(engine, *, profile: Profile, meter: str = "auto",
           floor: float | None = None, log=print) -> Verification:
    """Run the four stages on one engine and return a verdict.

    `floor` is the session's calibrated noise floor, used when the profile does
    not measure its own canary.
    """
    result = Verification(case_file=engine.subject, reps=profile.reps,
                          relaxations=engine.relaxations, profile=profile.name,
                          stubbed=engine.stubbed)

    log("equivalence")
    for note in result.relaxations:
        log(f"  RELAXED: {note}")
    rows = engine.check()
    for row in rows:
        kind = "" if row.measured else "  (check only)"
        note = " (mutates its arguments: fresh input per call)" if row.mutates and row.measured else ""
        log(f"  {row.label:<14} {'ok' if not row.difference else 'DIFFERS'}{kind}{note}")
        if row.difference:
            log(f"  {'':<14} {row.difference}")
    broken = [row for row in rows if row.difference]
    if broken:
        result.status = "not_equivalent"
        result.reason = (
            f"the repair behaves differently on {broken[0].label!r}: "
            f"{broken[0].difference}. The repair is wrong; fix it and re-run. "
            f"Do not report this candidate either way."
        )
        return result

    result.per_case = [CaseOutcome(label=row.label, equivalent=True, mutates_args=row.mutates)
                       for row in rows if row.measured]

    log("\nsizing")
    for index, outcome in enumerate(result.per_case):
        outcome.before_spc = engine.time(index, "before")
        outcome.after_spc = engine.time(index, "after")
        outcome.seconds_per_call = max(outcome.before_spc, outcome.after_spc)
        outcome.repeats, outcome.reps, outcome.clamped = _size(
            outcome.before_spc, outcome.after_spc, profile.window, profile.reps,
            profile.slow_factor,
        )
        note = (f"  CLAMPED to keep the slow side under {profile.slow_factor * profile.window:g}s"
                if outcome.clamped else "")
        log(f"  {outcome.label:<14} before {_duration(outcome.before_spc):>10}/call"
            f"  after {_duration(outcome.after_spc):>10}/call"
            f"  ->  {outcome.repeats:,} repeats{note}")

    engine.warm(profile.warmup)
    log(f"\nmeasurement  ({profile.reps} paired reps, ~{profile.window:g}s windows)")
    plans = [{"index": index, "repeats": outcome.repeats, "mutates": outcome.mutates_args,
              "reps": outcome.reps} for index, outcome in enumerate(result.per_case)]
    for outcome, comparison in zip(result.per_case, engine.measure(plans, meter=meter)):
        outcome.record(comparison)
        result.note_coverage(meter, comparison.domains, log)
        log(f"  {outcome.label:<14} {outcome.energy_saved_pct:+7.2f}% energy "
            f"+-{outcome.energy_ci_pct:.2f}%   "
            f"{'significant' if outcome.significant else 'not significant':<16}"
            f"time {outcome.time_saved_pct:+.2f}% +-{outcome.time_ci_pct:.2f}%")

    if profile.canary and result.per_case:
        # The floor has to be measured on one case, and measuring it on every
        # case would roughly double the run. Pick the case whose windows carry
        # the most energy, taking each variant at whichever of the two is
        # larger: a repair that regresses spends more in `after`, and choosing
        # on `before` alone would assume the answer.
        index, subject = max(enumerate(result.per_case),
                             key=lambda pair: max(pair[1].before_energy_j, pair[1].after_energy_j))
        result.canary_case = subject.label
        reading = engine.floor(plans[index], meter=meter)
        result.noise_floor_pct = abs(reading.energy_saved_pct) + reading.energy_ci_pct
        result.floor_source = f"canary on {subject.label!r}"
        log(f"\nnoise floor  ({subject.label}, original against itself)"
            f"  +-{result.noise_floor_pct:.2f}%")
    elif floor is not None:
        result.noise_floor_pct = floor
        result.floor_source = "session calibration"
        log(f"\nnoise floor  +-{floor:.2f}% (session calibration)")

    _decide(result)
    return result


def _harmful_cases(result: Verification) -> list[CaseOutcome]:
    """Cases the repair measurably hurts, each judged on its own.

    Two tests, and both are about this case alone. The loss has to be
    statistically separable from zero, and it has to clear the host's noise
    floor -- the same bar a saving has to clear. Without that symmetry the rig
    can refuse to call a saving real at 2% and still let a 2% loss sink the
    verdict, which is contamination deciding the answer in one direction only.

    There is deliberately no cross-case scale test any more. One used to
    require a loss to be worth some fraction of the most expensive case's
    per-call energy, so that a large percentage on a trivial input could not
    veto a real saving elsewhere. That mattered when the corpus was full of
    inputs like `[]`, where any repair looks catastrophic in relative terms and
    costs nanojoules in absolute ones. Those cases are gone, and each case now
    reports its own joules, so a reader can weigh the magnitudes without the
    verdict having done it for them.
    """
    return [
        case for case in result.per_case
        if case.significant
        and case.energy_saved_pct < 0
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
    if not result.per_case:
        result.status = "error"
        result.reason = "no case was measured."
        return

    helped = _helped_cases(result)
    hurt = _harmful_cases(result)
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
        biggest = max(result.per_case, key=lambda c: abs(c.energy_saved_pct))
        result.reason = (
            f"this host's noise floor measured {floor:.1f}%, above the "
            f"{USABLE_FLOOR_PCT:.1f}% needed to resolve anything here -- the "
            f"largest reading across {len(result.per_case)} cases was "
            f"{biggest.energy_saved_pct:+.1f}% on {biggest.label!r}. The canary "
            f"compares identical code against itself, so that floor is "
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
    return reason


def _mixed_reason(
    result: Verification, helped: list[CaseOutcome], hurt: list[CaseOutcome]
) -> str:
    """A trade-off: real on both sides, so the report needs both named."""
    best = max(helped, key=lambda c: c.energy_saved_pct)
    worst = max(hurt, key=lambda c: abs(c.excess_energy_per_call))
    return (
        f"a trade-off, not a fix: {best.energy_saved_pct:.1f}% saved on "
        f"{best.label!r} but {abs(worst.energy_saved_pct):.1f}% lost on "
        f"{worst.label!r}, both clearing the {result.noise_floor_pct:.1f}% "
        f"noise floor. Whether it pays depends on which input the code actually "
        f"sees, so the card must name both cases and let the agent judge."
    )


def _regressed_reason(result: Verification, hurt: list[CaseOutcome]) -> str:
    """Worse everywhere it measurably moved."""
    worst = max(hurt, key=lambda c: abs(c.excess_energy_per_call))
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
          reps: int, slow_factor: float) -> tuple[int, int, bool]:
    """Repeat count, repetitions, and whether the slow side forced a clamp.

    Both variants run the same number of calls -- that is what makes the
    comparison fair -- so there is one count to choose, and it is chosen from
    the *faster* variant. The faster one is the only side at risk of a window
    too short to resolve; the slower one is already over-resolved by being
    slow, and giving it a full window on its own terms would mean comparing
    different amounts of work.

    The count is clamped to keep the slow side inside `slow_factor` windows,
    which means the fast side then gets less than a full window. That looks like
    a compromise and is not. A full window exists to stop noise swamping a
    *small* difference; a small difference means the two run at similar speeds,
    the ratio is near one, and nothing is clamped. Clamping happens only when
    the ratio is large -- and then the saving is large too, and the answer is
    set by the large, well-resolved side. At a ratio of ten, the slow side
    reads ten times the fast side's energy; even if the short side were wrong
    by a quarter, a 90% saving would read 87.5% or 92.5%. The more the clamp
    costs in window length, the less that length matters.
    """
    fast = min(before_spc, after_spc)
    slow = max(before_spc, after_spc)
    budget = slow_factor * window

    wanted = choose_repeats(fast, window)
    if slow <= 0:
        return wanted, reps, False

    affordable = max(1, int(budget / slow))
    if wanted <= affordable:
        return wanted, reps, False

    # One call of the slow side already costs more than the whole budget, so
    # there is nothing left to trim from the count. Trim the repetitions
    # instead: the effect that makes a case this lopsided is not one a wider
    # interval will hide.
    if affordable <= 1 and slow > budget:
        return 1, min(reps, REDUCED_REPS), True
    return affordable, reps, True


def _time_one_call(case_file: CaseFile, case: Case, name: str = "before") -> float:
    """Seconds per call of one variant, used only to size the measured window."""
    function = case_file.variant(name)
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


# -- calibration -----------------------------------------------------------


def _calibration_path(profile: Profile) -> Path:
    return Path(tempfile.gettempdir()) / f"energy-smells-calibration-{profile.name}.json"


def calibrate(profile: Profile, meter: str = "auto", log=print) -> dict:
    """This host's resolution limit, measured the way submissions are measured.

    Two copies of identical code, alternating windows -- a submission whose
    repair changes nothing. The true answer is zero, so whatever it reads is
    contamination, and its width is the bar every real effect has to clear.
    """
    log(f"calibrating ({profile.name} profile): two copies of identical code, "
        f"which must come back insignificant.")
    work = Path(tempfile.mkdtemp(prefix="energy-calibration-"))
    try:
        repo = work / "repo"
        repo.mkdir()
        (repo / "canary.py").write_text(CANARY_CASE.read_text())
        source = (repo / "canary.py").read_text()
        body = source[source.index("def before"):source.index("def after")].strip()
        record = {
            "id": "calibration",
            "unit": "canary.py::before",
            "changed": {"canary.py::before": body},
            "cases_source": "from canary import cases\n\ndef checks():\n    return cases()\n",
        }
        engine = PairEngine(repo, record, work / "pair", meter=meter, require_counts=False)
        try:
            spc = engine.time(0, "before")
            repeats = choose_repeats(spc, profile.window)
            engine.warm(profile.warmup)
            reading = engine.measure([{"index": 0, "repeats": repeats, "mutates": False,
                                       "reps": CALIBRATION_REPS}], meter=meter)[0]
        finally:
            engine.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)

    payload = {
        "profile": profile.name,
        "noise_floor_pct": round(abs(reading.energy_saved_pct) + reading.energy_ci_pct, 2),
        "apparent_saving_pct": round(reading.energy_saved_pct, 2),
        "ci_pct": round(reading.energy_ci_pct, 2),
        "usable": not reading.energy_significant,
        "host": platform.node(),
        "measured_at": time.time(),
    }
    _calibration_path(profile).write_text(json.dumps(payload, indent=1))
    return payload


def session_floor(profile: Profile, meter: str, log) -> float:
    """The calibrated floor, measuring it first if none is fresh."""
    path = _calibration_path(profile)
    try:
        stored = json.loads(path.read_text())
        fresh = (stored.get("host") == platform.node()
                 and time.time() - stored.get("measured_at", 0) < CALIBRATION_TTL_S)
    except (OSError, ValueError):
        stored, fresh = {}, False
    if not fresh:
        stored = calibrate(profile, meter, log)
        log(f"  noise floor +-{stored['noise_floor_pct']:.2f}%"
            f"{'' if stored['usable'] else '  (NOT usable: identical code measured as different)'}\n")
    return float(stored["noise_floor_pct"])


# -- entry point -----------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", type=Path, nargs="?",
                        help="submissions (.jsonl), or a validation case file (.py)")
    parser.add_argument("--repo", type=Path, default=Path("."),
                        help="the repository the submissions were written against")
    parser.add_argument("--calibrate", action="store_true",
                        help="measure this host's noise floor and stop")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-record", action="store_true",
                        help="do not write measurements back into the submissions file")
    parser.add_argument("--reps", type=int, help="override the profile's repetitions")
    parser.add_argument("--window", type=float, help="override the profile's window, in seconds")
    parser.add_argument("--meter", default="auto")
    parser.add_argument("--no-canary", action="store_true",
                        help="skip the per-run canary (case files; faster, less trustworthy)")
    args = parser.parse_args(argv)

    is_case_file = args.target is not None and args.target.suffix == ".py"
    profile = PROFILES["validation" if is_case_file else "fast"]
    if args.reps or args.window or args.no_canary:
        profile = Profile(profile.name, args.window or profile.window,
                          args.reps or profile.reps,
                          profile.canary and not args.no_canary, profile.warmup,
                          profile.slow_factor)

    if args.calibrate:
        payload = calibrate(profile, args.meter, log=(lambda *a: None) if args.json else print)
        if args.json:
            print(json.dumps(payload, indent=1))
        else:
            print(f"  apparent saving {payload['apparent_saving_pct']:+.2f}% "
                  f"+-{payload['ci_pct']:.2f}%")
            print(f"\n{'OK' if payload['usable'] else 'FAIL'}: this host resolves about "
                  f"{payload['noise_floor_pct']:.1f}% with the {profile.name} profile."
                  + ("" if payload["usable"] else
                     " Identical code measured as different -- something else is running."))
        return 0 if payload["usable"] else 1
    if args.target is None:
        parser.error("give submissions (.jsonl), a case file (.py), or --calibrate")
    if is_case_file:
        return _run_case_file(args, profile)
    return _run_submissions(args, profile)


def _run_case_file(args, profile: Profile) -> int:
    """One of our own validation files, defining `before`, `after` and `cases`."""
    log = (lambda *a, **k: None) if args.json else print
    try:
        engine = CaseFileEngine(args.target)
        result = verify(engine, profile=profile, meter=args.meter, log=log)
        payload = result.to_dict()
    except (CaseFileError, MeasurementError) as exc:
        payload = {"status": "error", "reason": str(exc), "case_file": str(args.target)}
    if args.json:
        json.dump(payload, sys.stdout, indent=1)
        print()
    else:
        print(f"\nVERDICT: {payload['status']}\n  {payload['reason']}")
    return 0 if payload["status"] == "confirmed" else (2 if payload["status"] == "error" else 1)


def _run_submissions(args, profile: Profile) -> int:
    """Every line of a submissions file, each against the repository as it stands.

    Each is measured independently: a fresh pristine copy and a fresh patched
    copy per line, so no repair is measured on top of another. Unless
    `--no-record` is given, each line's result is written back into the file as
    `agent_measurement`, and a line whose content has not changed since is not
    measured again.
    """
    log = (lambda *a, **k: None) if args.json else print
    repo = args.repo.resolve()
    path = args.target
    lines = path.read_text(encoding="utf-8").splitlines()
    records: list = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except ValueError as exc:
            records.append({"__unparsable__": number, "__error__": str(exc)})
    file_problems = validate_file(records)

    floor = None
    if not profile.canary:
        floor = session_floor(profile, args.meter, log)

    outputs = []
    for index, record in enumerate(records):
        if "__unparsable__" in record:
            outputs.append({"id": f"line {record['__unparsable__']}", "status": "invalid",
                            "reason": f"not valid JSON: {record['__error__']}"})
            continue
        sid = record.get("id") if isinstance(record, dict) else None
        log(f"\n=== {sid}  {record.get('unit', '?') if isinstance(record, dict) else ''}")
        digest = submission_hash(record) if isinstance(record, dict) else ""
        stored = record.get("agent_measurement") if isinstance(record, dict) else None
        if not args.no_record and isinstance(stored, dict) and stored.get("status"):
            unchanged = stored.get("submission_hash") == digest
            if unchanged and stored["status"] not in REMEASURED:
                log(f"  already measured: {stored['status']}")
                outputs.append(stored)
                continue
            if not unchanged and stored["status"] in FINAL:
                # The stored measurement is left exactly as it was.
                reason = (f"this line was already measured ({stored['status']}) and has "
                          f"since been edited. A measured result is final: restore the "
                          f"line as it was, and submit a different repair as a new line "
                          f"listed in `related`.")
                log(f"  INVALID: {reason}")
                outputs.append({"id": sid, "status": "invalid", "reason": reason})
                continue

        payload = _measure_one(record, repo, profile, args.meter, floor,
                               file_problems.get(sid), log)
        payload["submission_hash"] = digest
        outputs.append(payload)
        log(f"\nVERDICT: {payload['status']}\n  {payload['reason']}")
        if not args.no_record and isinstance(record, dict):
            record["agent_measurement"] = payload
            _rewrite(path, records)

    if args.json:
        json.dump(outputs, sys.stdout, indent=1)
        print()
    statuses = {o.get("status") for o in outputs}
    if statuses & {"invalid", "error"}:
        return 2
    return 0 if statuses <= {"confirmed"} else 1


def _measure_one(record, repo: Path, profile: Profile, meter: str,
                 floor: float | None, file_problem: str | None, log) -> dict:
    """One submission, start to finish, as a result row. Never raises."""
    sid = record.get("id", "?") if isinstance(record, dict) else "?"
    problem = validate(record) or file_problem
    if problem:
        return {"id": sid, "status": "invalid", "reason": problem}

    work = Path(tempfile.mkdtemp(prefix=f"energy-submission-{sid}-"))
    engine = None
    try:
        engine = PairEngine(repo, record, work, meter=meter)
        result = verify(engine, profile=profile, meter=meter, floor=floor, log=log)
        payload = {"id": sid, "unit": record["unit"], **result.to_dict()}
        payload.pop("case_file", None)
        return payload
    except SubmissionError as exc:
        return {"id": sid, "status": "invalid", "reason": str(exc)}
    except WorkerError as exc:
        if exc.stub_used:
            return {"id": sid, "status": "error", "reason": (
                f"{exc}. The unit needs a library this environment does not have "
                f"installed; it cannot be measured here.")}
        return {"id": sid, "status": "error", "reason": str(exc)}
    except (MeasurementError, LoadError, OSError) as exc:
        return {"id": sid, "status": "error", "reason": str(exc)}
    finally:
        if engine is not None:
            engine.close()
        shutil.rmtree(work, ignore_errors=True)


def _rewrite(path: Path, records: list) -> None:
    """Write the submissions back, atomically, one object per line."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records
                if "__unparsable__" not in r),
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    sys.exit(main())
