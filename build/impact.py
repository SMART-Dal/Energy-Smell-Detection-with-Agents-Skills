"""Measured saving per root cause, which is the only thing that orders a scan.

A scanner that ranks by how many facts it found reports the cheapest smell
loudest, because the cheap ones are the ones with a syntactic shape common
enough to appear everywhere.  Ranking needs to key off what the repair is
actually worth, and we have that measured in `validation/results/`, so it is
read from there rather than graded by hand.

The statistic is the **mean saving across every measured shape of the root
cause, counting a shape that did not confirm as zero**.  Both halves of that
matter.  Averaging rather than taking the best keeps a root cause from being
floated by the one microbenchmark whose loop body is nothing but the thing
under test -- caching an attribute lookup reads 55% there and 1.8% in a
function that also does work.  Counting the failures as zero is what separates
a repair that always pays a little from one that pays hugely on some inputs and
costs on others: `expensive_operand_first` confirmed 89.6% on one shape and
regressed on two, and lands near a third of that.

A root cause whose shapes all came back `negligible`, `mixed` or
`regressed` comes out at zero.  That is
not a gap in the data; it is the data saying this repair does not reliably pay,
which is exactly what should sink it in a ranking.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RESULTS = Path("validation/results/taxonomy.jsonl")
"""Relative to the project root, which the caller passes in."""

CASE_STEM = re.compile(r"/(C\d+)S(\d+)_")


def root_cause_of(case_file: str) -> str | None:
    """`validation/taxonomy/C10S5_global_hoist.py` -> `C10.S5`."""
    found = CASE_STEM.search(case_file)
    return f"{found.group(1)}.S{found.group(2)}" if found else None


def measured_impact(results: Path = RESULTS, root: Path | None = None) -> dict[str, float]:
    """Mean saving per root cause, as a percentage, from the shapes that remain.

    Results outlive the case files that produced them -- a shape removed for
    measuring the wrong thing leaves its row behind -- so a row whose file is
    gone is skipped rather than counted.  Rebuilding after a measurement pass is
    what keeps this current.
    """
    base = root or Path.cwd()
    results = base / results if not results.is_absolute() else results
    if not results.exists():
        return {}

    savings: dict[str, list[float]] = {}
    for line in results.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        case = row.get("case_file", "")
        if not (base / case).exists():
            continue
        root_cause = root_cause_of(case)
        if root_cause is None:
            continue
        savings.setdefault(root_cause, []).append(_saving_pct(row))

    return {
        root_cause: round(sum(values) / len(values), 1)
        for root_cause, values in savings.items()
    }


MIN_MEASURED_CHANGE = 15.0
"""Below this, a root cause's repair is treated as having no effect.

A root cause is reported by the scan only if at least one input of one of its
measured samples changed energy by this much, either way (`measured_reach`).
Under it on every input of every sample, the repair did nothing a reader would
notice even on the microbenchmark built to show it, and on real code -- where
the loop also does other work -- it does less. Javad set the line at 15%."""


def measured_reach(results: Path = RESULTS, root: Path | None = None) -> dict[str, float]:
    """The largest change, either way, that any input of any sample produced.

    Per root cause, as a percentage of the `before` energy: +60 for a repair
    that saved 60% on its best input, 300 for one that cost three times as much
    on its worst. Unlike `measured_impact` it counts every row whatever its
    verdict, because the question it answers is not "does this repair pay" but
    "did this repair ever move anything" -- and a root cause whose answer is
    under `MIN_MEASURED_CHANGE` on every input of every sample is not reported by
    the scan at all.
    """
    base = root or Path.cwd()
    results = base / results if not results.is_absolute() else results
    if not results.exists():
        return {}

    reach: dict[str, float] = {}
    for line in results.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        case = row.get("case_file", "")
        if not (base / case).exists():
            continue
        root_cause = root_cause_of(case)
        if root_cause is None:
            continue
        for measured in row.get("per_case", []):
            before = measured.get("before_energy_j") or 0.0
            after = measured.get("after_energy_j") or 0.0
            if before > 0:
                change = abs(100.0 * (before - after) / before)
                reach[root_cause] = max(reach.get(root_cause, 0.0), change)
    return {root_cause: round(value, 1) for root_cause, value in reach.items()}


def _saving_pct(row: dict) -> float:
    """Percentage of energy a confirmed row saved, or zero.

    Results store what was measured -- joules for each variant, on each case --
    rather than a percentage derived from them, and no case is promoted to
    stand for the file. So the figure is the total across every case measured:
    all the joules `before` spent against all the joules `after` spent.

    Totalling is what makes this weight the cases correctly without nominating
    one. A case whose window carries two hundred joules contributes two hundred
    times what a case carrying one does, which is the right answer for "what is
    this repair worth" and is exactly what picking a single expensive case used
    to approximate.

    Any status other than `confirmed` counts as zero: a repair that pays only
    on some inputs (`mixed`), or does nothing measurable (`negligible`), must
    not be ranked as though it always pays.
    """
    if row.get("status") != "confirmed":
        return 0.0
    before = sum(c.get("before_energy_j") or 0.0 for c in row.get("per_case", []))
    after = sum(c.get("after_energy_j") or 0.0 for c in row.get("per_case", []))
    if before <= 0:
        return 0.0
    return max(0.0, 100.0 * (before - after) / before)
