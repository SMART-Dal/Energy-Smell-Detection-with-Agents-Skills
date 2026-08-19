"""Rebuild the `reason` text of every `regressed` row from its own data.

The verdict and every number were computed correctly -- the deciding case is
chosen by measured per-call cost, not by label -- but the summary sentence was a
fixed template asserting two things it had not checked: that the deciding case
was called "large", and that the repair had helped it. Sixteen of the first
twenty-one rows said the repair helped a case it had made worse.

Nothing is re-measured, and nothing is re-decided. The worst case and the
percentage-of-deciding-cost term are lifted out of the old sentence rather than
recomputed, because the verdict picked the worst case by *absolute* extra work
per call and `per_case` does not carry timings -- re-picking it by percentage
would silently choose a different case, usually the tiny one the tolerance rule
exists to discount.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# "... costs 12.5% on 'all-distinct' -- worth 12.4% of the deciding case's own"
OLD = re.compile(r"costs ([\d.]+)% on '([^']+)' -- worth ([\d.]+)% of")


def rebuild(row: dict) -> str | None:
    found = OLD.search(row.get("reason", ""))
    if not found:
        return None
    worst_pct, worst_label, cost_pct = found.group(1), found.group(2), found.group(3)

    deciding_label = row.get("deciding_case", "")
    per_case = {c["label"]: c for c in row.get("per_case", ())}
    deciding = per_case.get(deciding_label, {})
    decided = deciding.get("energy_saved_pct", 0.0)
    gained = [c["label"] for c in row.get("per_case", ())
              if c["significant"] and c["energy_saved_pct"] > 0]

    # The share-of-deciding-cost figure says "this loss is real work, not a
    # ratio on a microsecond input". It means nothing when the case that lost
    # *is* the deciding case, where the share is ~100% by construction.
    if worst_label == deciding_label:
        loss = f"{worst_pct}% lost on it"
        elsewhere = ""
    else:
        loss = (f"{worst_pct}% lost on {worst_label!r}, worth {cost_pct}% of "
                f"{deciding_label!r}'s own per-call cost, so it is real work "
                f"and not rounding")
        elsewhere = f" and {loss}"

    if deciding.get("significant") and decided > 0:
        return (
            f"a trade-off rather than a fix: {decided:.1f}% saved on "
            f"{deciding_label!r}, the case that dominates the cost, against "
            f"{loss}. Report under `refuted` and name both cases."
        )
    if gained:
        helped = ", ".join(repr(label) for label in gained)
        return (
            f"the repair helps {helped}, but not {deciding_label!r}, the case "
            f"that dominates the cost, which read {decided:+.1f}%"
            f"{elsewhere}. Report under `refuted` and say which inputs it is for."
        )
    return (
        f"no case improved: {deciding_label!r}, the case that dominates the "
        f"cost, read {decided:+.1f}%{elsewhere}. The repair costs more than the "
        f"code it replaces on every input measured; report under `refuted`."
    )


def main(path: Path, apply: bool) -> int:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    changed = 0
    for row in rows:
        if row.get("status") != "regressed":
            continue
        fresh = rebuild(row)
        if fresh and fresh != row.get("reason"):
            changed += 1
            if apply:
                row["reason"] = fresh
            else:
                print(f"{Path(row['case_file']).stem}\n    {fresh}\n")
    if apply:
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{changed} regressed rows {'rewritten' if apply else 'would change'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), "--apply" in sys.argv))
