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

A root cause whose shapes all refuted or regressed comes out at zero.  That is
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
        confirmed = (
            row.get("status") == "confirmed"
            and row.get("energy_saved_pct") is not None
        )
        savings.setdefault(root_cause, []).append(
            max(0.0, float(row["energy_saved_pct"])) if confirmed else 0.0
        )

    return {
        root_cause: round(sum(values) / len(values), 1)
        for root_cause, values in savings.items()
    }
