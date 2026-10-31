"""RQ2: which root causes and categories agents found, and which repairs saved energy.

The unit of counting is an INSTANCE: one root cause in one unit, e.g.
(dx-toolkit, resolver.py::split_unescaped, C7.S1). RQ2 asks how common a root
cause is in real code, so an instance counts once, however many runs found it
and however many repairs were written for it.

Only the 12 runs of the two taxonomy skills label smells and repairs with a root
cause, so only they are used.

For each instance:
  found       some run accepted it as a smell in step 2 (record/steps/step2.jsonl)
  found_by    how many of the four taxonomy runs on its repository accepted it
  repaired    some run submitted a repair for it (review/results.jsonl)
  measured    some repair of it was measured (verdict in MEASURED)
  outcome     the best verdict among its measured repairs, in the order
              confirmed > partial > mixed > negligible > regressed.
              The instance is CONFIRMED when the best verdict is confirmed or
              partial, i.e. when at least one repair saved energy.
  best saving the largest saving among its confirmed repairs

The repairs in analysis/excluded_repairs.csv count as measured, with the status
"excluded" (common.review_results()); it is none of the verdicts below.

Writes to analysis/output/rq2/:
  instances.csv              one row per instance
  root_causes.csv            one row per root cause with at least one instance
  root_causes_table.csv      the root causes with at least 3 measured instances
  categories.csv             one row per category (C1 to C12)
  summary.json               totals

Run:  python3 analysis/rq2_root_causes.py
"""

import re

from common import (MEASURED, OUTPUT_DIR, REPOS, ROOT, SAVES, all_runs, category_of, median,
                    percent, read_jsonl, review_results, run_folder, write_csv, write_json)
from rq1_step2 import smells_of

OUT = OUTPUT_DIR / "rq2"   # where this script writes
TAXONOMY = ROOT / "dist" / "full" / "energy-smells" / "reference" / "README.md"

# Verdicts from best to worst: an instance takes the best verdict of its repairs
VERDICT_ORDER = ["confirmed", "partial", "mixed", "negligible", "regressed"]

MIN_MEASURED = 3            # root causes in the RQ2 table have at least this many measured instances


def taxonomy_names():
    """{'C1': 'Redundant Computation', 'C1.S1': 'Dead Code', ...} from the taxonomy README."""
    names = {}
    for line in TAXONOMY.read_text().splitlines():
        found = re.match(r"\| \*\*(C\d+(?:\.S\d+)?)\*\* \| ([^|]+) \|", line)
        if found:
            names[found.group(1)] = found.group(2).strip()
    return names


def collect_instances():
    """{(repo, unit, root cause): {"runs": set of runs, "repairs": [repairs]}}.

    Also returns how many repairs name a (unit, root cause) that no run accepted.
    """
    instances = {}
    for repo, skill, model in all_runs():
        if skill == "control":                          # Unguided has no root causes
            continue
        for smell in smells_of(repo, skill, model):     # the accepted suspicions
            cause = smell.get("root_cause")
            if not cause:
                continue
            key = (repo, smell["unit"], cause)
            if key not in instances:
                instances[key] = {"runs": set(), "repairs": []}
            instances[key]["runs"].add((skill, model))

    outside = 0                                         # repairs of a pair no run accepted
    for repo, skill, model in all_runs():
        if skill == "control":
            continue
        for repair in review_results(repo, skill, model):
            cause = repair.get("root_cause")
            if not cause:
                continue
            key = (repo, repair["unit"], cause)
            repair["run"] = (repo, skill, model)            # remember which run wrote it
            if key in instances:
                instances[key]["repairs"].append(repair)
            else:
                outside = outside + 1
    return instances, outside


def instance_row(key, data):
    """The outcome of one instance, as a dictionary."""
    repo, unit, cause = key
    measured = []                                       # its measured repairs
    for repair in data["repairs"]:
        if repair["status"] in MEASURED:
            measured.append(repair)

    best_verdict = None
    for verdict in VERDICT_ORDER:                       # the first verdict any repair reached
        if any(repair["status"] == verdict for repair in measured):
            best_verdict = verdict
            break

    confirmed_savings = []                              # for the best saving
    for repair in measured:
        if repair["status"] in SAVES:
            confirmed_savings.append(repair["mean_saving_pct"])

    verdicts = {repair["status"] for repair in measured}
    row = {}
    row["repo"] = repo
    row["unit"] = unit
    row["root_cause"] = cause
    row["category"] = category_of(cause)
    row["found_by_runs"] = len(data["runs"])
    row["repairs"] = len(data["repairs"])
    row["measured_repairs"] = len(measured)
    row["repaired"] = len(data["repairs"]) > 0
    row["measured"] = len(measured) > 0
    row["best_verdict"] = best_verdict or ""
    row["confirmed"] = best_verdict in SAVES
    row["best_saving_pct"] = round(max(confirmed_savings), 1) if confirmed_savings else None
    # Do its repairs disagree: some confirmed, some not?
    row["repairs_disagree"] = bool(verdicts & SAVES) and bool(verdicts - SAVES)
    return row


def summary_of(rows, key_name, key_value, name):
    """Counts for one root cause or category, from its instance rows."""
    confirmed = [r for r in rows if r["confirmed"]]
    savings = [r["best_saving_pct"] for r in confirmed]
    measured = [r for r in rows if r["measured"]]
    line = {key_name: key_value, "name": name}
    line["instances"] = len(rows)
    for repo in REPOS:                                  # where the instances are
        line["instances_" + repo] = len([r for r in rows if r["repo"] == repo])
    line["found_by_2_or_more_runs"] = len([r for r in rows if r["found_by_runs"] >= 2])
    line["repaired"] = len([r for r in rows if r["repaired"]])
    line["pct_repaired"] = percent(line["repaired"], len(rows))    # how often the agents chose to repair
    line["measured"] = len(measured)
    line["confirmed"] = len(confirmed)
    line["confirmed_per_100_instances"] = percent(len(confirmed), len(rows))
    line["pct_measured_confirmed"] = percent(len(confirmed), len(measured))
    line["median_best_saving_pct"] = round(median(savings), 1) if savings else None
    line["best_mixed"] = len([r for r in measured if r["best_verdict"] == "mixed"])
    line["best_negligible"] = len([r for r in measured if r["best_verdict"] == "negligible"])
    line["best_regressed"] = len([r for r in measured if r["best_verdict"] == "regressed"])
    return line


def cause_sort_key(cause):
    """C3.S10 after C3.S9: sort by the two numbers, not by the text."""
    category, number = cause.split(".S")
    return (int(category[1:]), int(number))


def main():
    names = taxonomy_names()
    instances, outside = collect_instances()

    rows = []
    for key in sorted(instances, key=lambda k: (k[0], k[1], cause_sort_key(k[2]))):
        rows.append(instance_row(key, instances[key]))
    write_csv(rows, OUT / "instances.csv")

    # One row per root cause, most instances first
    by_cause = {}
    for row in rows:
        by_cause.setdefault(row["root_cause"], []).append(row)
    causes = []
    for cause in sorted(by_cause, key=cause_sort_key):
        causes.append(summary_of(by_cause[cause], "root_cause", cause, names.get(cause, "")))
    write_csv(causes, OUT / "root_causes.csv")

    # The RQ2 table: root causes with at least MIN_MEASURED measured instances,
    # ordered by how many instances were found
    table = [c for c in causes if c["measured"] >= MIN_MEASURED]
    table.sort(key=lambda c: (-c["instances"], cause_sort_key(c["root_cause"])))
    write_csv(table, OUT / "root_causes_table.csv")

    # One row per category, C1 to C12, and the totals
    categories = []
    for number in range(1, 13):
        category = "C" + str(number)
        in_category = [r for r in rows if r["category"] == category]
        categories.append(summary_of(in_category, "category", category, names[category]))
    categories.append(summary_of(rows, "category", "All", "All"))
    write_csv(categories, OUT / "categories.csv")

    summary = {}
    summary["instances"] = len(rows)
    summary["found_by_2_or_more_runs"] = len([r for r in rows if r["found_by_runs"] >= 2])
    summary["repaired"] = len([r for r in rows if r["repaired"]])
    summary["measured"] = len([r for r in rows if r["measured"]])
    summary["confirmed"] = len([r for r in rows if r["confirmed"]])
    summary["instances_with_2_or_more_measured_repairs"] = len([r for r in rows if r["measured_repairs"] >= 2])
    summary["instances_whose_repairs_disagree"] = len([r for r in rows if r["repairs_disagree"]])
    # Taking the best repair favours instances repaired more than once: compare the two groups
    several = [r for r in rows if r["measured_repairs"] >= 2]
    once = [r for r in rows if r["measured_repairs"] == 1]
    summary["pct_confirmed_measured_2_or_more"] = percent(len([r for r in several if r["confirmed"]]), len(several))
    summary["pct_confirmed_measured_once"] = percent(len([r for r in once if r["confirmed"]]), len(once))
    summary["root_causes_found"] = len(causes)
    summary["root_causes_confirmed"] = len([c for c in causes if c["confirmed"] > 0])
    summary["root_causes_in_table"] = len(table)
    summary["categories_found"] = len([c for c in categories[:-1] if c["instances"] > 0])
    summary["repairs_of_a_pair_no_run_accepted"] = outside
    write_json(summary, OUT / "summary.json")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
