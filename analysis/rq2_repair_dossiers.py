"""RQ2: every repair of each frequent root cause, written out to be read.

How agents repair a root cause cannot be counted from the code alone, so this
script prepares the material for reading. For every root cause in the RQ2 table
(at least 3 measured instances, see rq2_root_causes.py) it writes one file with
all its measured repairs, grouped by instance (one root cause in one unit).

Within an instance, repairs whose code is identical (all whitespace removed) are
one EDIT: several runs wrote the same thing. Each edit is shown once, with the
verdicts and savings of every run that measured it, the lines it changed, the
calls it removed and added, and a diff of the function before and after. The
diff compares the two versions as Python rewrites them (ast.unparse), so
comments and formatting do not show up as changes.

The strategies are then named by hand in analysis/rq2_strategy_coding.csv
(one row per edit), and summarised by rq2_strategies.py.

Reads review/results.jsonl (through common.review_results()) and
review/submissions.jsonl of the 12 taxonomy runs,
the untouched repositories (through rq1_repairs.py), and output/rq2/instances.csv.

Writes to analysis/output/rq2/:
  dossiers/<root cause>.md   all edits of that root cause, to read
  edits.csv                  one row per edit: instance, runs, verdicts, savings,
                             lines changed, calls removed and added. best_saving_pct
                             is the best confirmed saving (empty if none was confirmed)

Run after rq2_root_causes.py:  python3 analysis/rq2_repair_dossiers.py
"""

import ast
import csv
import difflib

from common import (MEASURED, OUTPUT_DIR, SAVES, all_runs, read_jsonl, review_results,
                    run_folder, write_csv)
from rq1_repairs import (lines_changed, normalized_lines, original_function,
                         repaired_function)

OUT = OUTPUT_DIR / "rq2"   # where this script writes


def table_root_causes():
    """The root causes of the RQ2 table, from root_causes_table.csv."""
    with open(OUT / "root_causes_table.csv") as handle:
        return [row["root_cause"] for row in csv.DictReader(handle)]


def call_names(function):
    """{call name: how often} in a function, e.g. {'join': 1, 'append': 2}."""
    counts = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):     # obj.method(...)
                name = node.func.attr
            elif isinstance(node.func, ast.Name):        # function(...)
                name = node.func.id
            else:
                continue
            counts[name] = counts.get(name, 0) + 1
    return counts


def calls_difference(before, after):
    """Calls the repair removed and added, as two texts like 'append x2, find'."""
    removed = []
    added = []
    for name in sorted(set(before) | set(after)):
        change = after.get(name, 0) - before.get(name, 0)
        if change < 0:
            removed.append(name if change == -1 else f"{name} x{-change}")
        if change > 0:
            added.append(name if change == 1 else f"{name} x{change}")
    return ", ".join(removed), ", ".join(added)


def collect_edits(causes):
    """{root cause: {(repo, unit): {code: edit}}} for the measured repairs of these root causes."""
    edits = {}
    for repo, skill, model in all_runs():
        if skill == "control":                          # Unguided has no root causes
            continue
        folder = run_folder(repo, skill, model)
        submissions = {}
        for submission in read_jsonl(folder / "review" / "submissions.jsonl"):
            submissions[submission["id"]] = submission
        for repair in review_results(repo, skill, model):
            cause = repair.get("root_cause")
            if cause not in causes or repair["status"] not in MEASURED:
                continue
            changed = submissions[repair["id"]]["changed"]
            code = " | ".join(u + ":" + "".join(c.split()) for u, c in sorted(changed.items()))
            instance = (repo, repair["unit"])
            by_instance = edits.setdefault(cause, {}).setdefault(instance, {})
            if code not in by_instance:                 # the first time this edit is seen
                by_instance[code] = {"changed": changed, "measurements": []}
            by_instance[code]["measurements"].append({
                "run": f"{skill}/{model}", "repair": repair["id"],
                "verdict": repair["status"],
                "saving": None if repair["mean_saving_pct"] is None else round(repair["mean_saving_pct"], 1)})
    return edits


def describe(repo, unit, changed):
    """Lines changed, calls removed and added, and the diff of the repaired unit."""
    lines = 0
    for name, code in changed.items():                  # every function the edit touches
        after = normalized_lines(repaired_function(code))
        original = original_function(repo, name)
        lines = lines + (len(after) if original is None else
                         lines_changed(normalized_lines(original), after))
    before_fn = original_function(repo, unit)
    after_fn = repaired_function(changed[unit])
    removed, added = calls_difference(call_names(before_fn), call_names(after_fn))
    diff = list(difflib.unified_diff(normalized_lines(original_function(repo, unit)),
                                     normalized_lines(repaired_function(changed[unit])),
                                     lineterm="", n=1))[2:]   # drop the two file-name lines
    return lines, removed, added, diff


def main():
    causes = table_root_causes()
    edits = collect_edits(set(causes))
    (OUT / "dossiers").mkdir(parents=True, exist_ok=True)
    for old in (OUT / "dossiers").glob("*.md"):         # a root cause may have left the table
        old.unlink()

    rows = []                                           # edits.csv
    for cause in causes:
        text = [f"# {cause}: every measured edit, by instance", ""]
        for number, ((repo, unit), by_code) in enumerate(sorted(edits[cause].items()), start=1):
            text.append(f"## Instance {number}: {repo} :: {unit.split('::')[1]}")
            text.append(f"`{unit}`")
            text.append("")
            for letter, edit in zip("abcdefghij", by_code.values()):
                lines, removed, added, diff = describe(repo, unit, edit["changed"])
                measured = edit["measurements"]
                # The best saving: confirmed measurements only
                usable = [m["saving"] for m in measured if m["verdict"] in SAVES]
                best = max(usable) if usable else None
                verdicts = ", ".join(f"{m['run']} {m['verdict']}" + ("" if m["saving"] is None else f" {m['saving']}%")
                                     for m in measured)
                text.append(f"### Edit {number}{letter}: {lines} lines changed; {verdicts}")
                text.append(f"calls removed: {removed or '-'}; calls added: {added or '-'}")
                text.append("```diff")
                text.extend(diff)
                text.append("```")
                text.append("")
                rows.append({"root_cause": cause, "instance": number, "edit": f"{number}{letter}",
                             "repo": repo, "unit": unit, "runs": len(measured),
                             "verdicts": " ".join(m["verdict"] for m in measured),
                             "savings": " ".join("-" if m["saving"] is None else str(m["saving"]) for m in measured),
                             "confirmed": any(m["verdict"] in SAVES for m in measured),
                             "best_saving_pct": best, "lines_changed": lines,
                             "calls_removed": removed, "calls_added": added,
                             "repairs": " ".join(m["repair"] for m in measured)})
        (OUT / "dossiers" / f"{cause}.md").write_text("\n".join(text) + "\n")
    write_csv(rows, OUT / "edits.csv")
    print("wrote", OUT / "dossiers", "and", OUT / "edits.csv")


if __name__ == "__main__":
    main()
