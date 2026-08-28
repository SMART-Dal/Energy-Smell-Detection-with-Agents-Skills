"""Measured impact per root cause, for ranking what a scan reports first.

A scanner that ranks by how many facts it found reports the cheapest smell
loudest, because the cheap ones are the ones with a syntactic shape common
enough to appear everywhere.  Ranking needs a second axis: how much the repair
is actually worth.  We have that measured, in `validation/results/`, so it is
read from there rather than guessed.

The statistic is the **lowest** confirmed saving across a root cause's shapes,
not the highest and not the mean.  Every root cause has at least one case whose
loop body is nothing but the thing being measured, and those read high -- 55%
for caching an attribute lookup -- while the same repair in a function that also
does work reads 1.8%.  Real code is the second kind, so the low end is the
honest estimate and the high end is the microbenchmark.

A root cause whose shapes all refuted or regressed gets the bottom tier.  That
is not a gap in the data; it is the data saying this repair does not reliably
pay, which is exactly what should sink it in a ranking.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RESULTS = Path("validation/results/taxonomy.jsonl")
"""Relative to the project root, which the caller passes in."""

TIER_NONE, TIER_LOW, TIER_MEDIUM, TIER_HIGH = 1, 2, 3, 4

THRESHOLDS = ((40.0, TIER_HIGH), (10.0, TIER_MEDIUM), (0.0, TIER_LOW))
"""Lowest confirmed saving -> tier.  Wide buckets on purpose: the measurement
separates 2% from 45% reliably and 38% from 45% not at all."""

CASE_STEM = re.compile(r"/(C\d+)S(\d+)_")


def root_cause_of(case_file: str) -> str | None:
    """`validation/taxonomy/C10S5_global_hoist.py` -> `C10.S5`."""
    found = CASE_STEM.search(case_file)
    return f"{found.group(1)}.S{found.group(2)}" if found else None


def measured_impact(results: Path = RESULTS, root: Path | None = None) -> dict[str, int]:
    """Tier per root cause, from the case files that still exist.

    Results outlive the case files that produced them -- a shape removed for
    measuring the wrong thing leaves its row behind -- so a row whose file is
    gone is skipped rather than counted.  Rebuilding after a measurement pass
    is what keeps this current.
    """
    base = root or Path.cwd()
    results = base / results if not results.is_absolute() else results
    if not results.exists():
        return {}
    confirmed: dict[str, list[float]] = {}
    seen: set[str] = set()
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
        seen.add(root_cause)
        if row.get("status") == "confirmed" and row.get("energy_saved_pct") is not None:
            confirmed.setdefault(root_cause, []).append(float(row["energy_saved_pct"]))

    tiers = {rc: TIER_NONE for rc in seen}
    for root_cause, savings in confirmed.items():
        lowest = min(savings)
        tiers[root_cause] = next(
            tier for threshold, tier in THRESHOLDS if lowest >= threshold
        )
    return tiers
