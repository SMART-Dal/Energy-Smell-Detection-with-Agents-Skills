"""RQ1, by category and root cause: from accepted smells to confirmed repairs.

Only the 12 runs of the two taxonomy skills (Taxonomy+Rules and Taxonomy) are
used, because only they label a smell or a repair with a root cause (e.g.
C10.S4, in category C10). For each category, and for each root cause, we count:

  smells        suspicions accepted in step 2 (record/steps/step2.jsonl)
  deferred      smells the agent left unrepaired in step 3 (record/steps/step3.jsonl):
                outside the 20 repairs, or no inputs were asked for
  blocked       smells whose unit could not be measured here (no inputs could be
                generated, or the module does not load), as step 3 recorded them
  submitted     repairs submitted for it (review/results.jsonl, every line)
  measured      of those, repairs we measured (verdict in MEASURED)
  confirmed     of those, repairs that save energy (confirmed or partial)
  per_100       confirmed repairs per 100 smells: how often a smell of this kind
                ends as a confirmed repair. A run repairs at most 20 units, so
                most smells are never repaired; the number compares categories
                with each other and is not a success rate.
  median        median saving of the confirmed repairs, in percent

The names of the categories and root causes are read from the taxonomy the
agent used: dist/full/energy-smells/reference/README.md.

Writes to analysis/output/rq1/:
  categories_funnel.csv     one row per category
  root_causes_funnel.csv    one row per root cause with at least one smell
  root_causes_reasons.csv   for each root cause, the reasons the agents wrote for
                            smells they deferred or found blocked, with how often
                            each reason was written (the first 120 characters)
  categories_summary.json   totals over the 12 runs

Run:  python3 analysis/rq1_categories.py
"""

import re

from common import (MEASURED, OUTPUT_DIR, REPOS, ROOT, SAVES, all_runs, category_of, median,
                    percent, read_jsonl, run_folder, write_csv, write_json)
from rq1_step2 import smells_of

OUT = OUTPUT_DIR / "rq1"   # where this script writes
TAXONOMY = ROOT / "dist" / "full" / "energy-smells" / "reference" / "README.md"


def taxonomy_names():
    """{'C1': 'Redundant Computation', 'C1.S1': 'Dead Code', ...} from the taxonomy README.

    The README has one table row per category and per root cause, like
      | **C1** | Redundant Computation | ...
      | **C1.S1** | Dead Code | ...
    """
    names = {}
    for line in TAXONOMY.read_text().splitlines():
        found = re.match(r"\| \*\*(C\d+(?:\.S\d+)?)\*\* \| ([^|]+) \|", line)
        if found:
            names[found.group(1)] = found.group(2).strip()
    return names


def count_into(counts, key, field):
    """Add one to counts[key][field], creating the entry when it is missing."""
    if key not in counts:
        counts[key] = {"smells": 0, "deferred": 0, "blocked": 0, "submitted": 0,
                       "measured": 0, "confirmed": 0, "savings": []}
        for repo in REPOS:                              # smells found in each repository
            counts[key]["smells_" + repo] = 0
    counts[key][field] = counts[key][field] + 1


def funnel_counts():
    """Counts per category and per root cause, over the 12 taxonomy runs.

    Also returns {(root cause, outcome, reason): times written} for the smells
    that were deferred or blocked in step 3.
    """
    by_category = {}                                    # {'C10': {...}}
    by_cause = {}                                       # {'C10.S4': {...}}
    reasons = {}                                        # {(cause, outcome, reason): count}
    for repo, skill, model in all_runs():
        if skill == "control":                          # Unguided has no root causes
            continue
        folder = run_folder(repo, skill, model)

        # Step 2: the accepted smells, and the root cause of each (unit, label)
        cause_of = {}
        for smell in smells_of(repo, skill, model):
            cause = smell.get("root_cause")
            if not cause:
                continue
            cause_of[(smell["unit"], smell["label"])] = cause
            count_into(by_category, category_of(cause), "smells")
            count_into(by_cause, cause, "smells")
            count_into(by_category, category_of(cause), "smells_" + repo)
            count_into(by_cause, cause, "smells_" + repo)

        # Step 3: what the agent did with each smell (submitted, deferred, blocked)
        for record in read_jsonl(folder / "record" / "steps" / "step3.jsonl"):
            for step3 in record["outcomes"]:            # one outcome per suspicion
                cause = cause_of.get((record["unit"], step3["label"]))
                if cause is None or step3["outcome"] not in ("deferred", "blocked"):
                    continue                            # not a smell, or it was submitted
                count_into(by_category, category_of(cause), step3["outcome"])
                count_into(by_cause, cause, step3["outcome"])
                key = (cause, step3["outcome"], (step3.get("why") or "")[:120])
                reasons[key] = reasons.get(key, 0) + 1

        # Step 3: the repairs, and our verdict on each
        results = read_jsonl(folder / "review" / "results.jsonl")
        for repair in results:
            cause = repair.get("root_cause")
            if not cause:
                continue
            for counts, key in ((by_category, category_of(cause)), (by_cause, cause)):
                count_into(counts, key, "submitted")
                if repair["status"] in MEASURED:
                    count_into(counts, key, "measured")
                if repair["status"] in SAVES:
                    count_into(counts, key, "confirmed")
                    counts[key]["savings"].append(repair["mean_saving_pct"])
    return by_category, by_cause, reasons


def funnel_row(key, name, counts):
    """One table row from the counts of one category or root cause."""
    row = {}
    row["id"] = key
    row["name"] = name
    row["smells"] = counts["smells"]
    for repo in REPOS:
        row["smells_" + repo] = counts.get("smells_" + repo, 0)
    row["deferred"] = counts["deferred"]
    row["blocked"] = counts["blocked"]
    row["submitted"] = counts["submitted"]
    row["measured"] = counts["measured"]
    row["confirmed"] = counts["confirmed"]
    row["confirmed_per_100_smells"] = percent(counts["confirmed"], counts["smells"])
    savings = counts["savings"]
    row["median_saving_pct"] = round(median(savings), 1) if savings else None
    return row


def main():
    names = taxonomy_names()
    by_category, by_cause, reasons = funnel_counts()

    categories = []
    for number in range(1, 13):                         # C1 to C12, in order
        key = "C" + str(number)
        empty = {"smells": 0, "deferred": 0, "blocked": 0, "submitted": 0, "measured": 0,
                 "confirmed": 0, "savings": []}
        categories.append(funnel_row(key, names[key], by_category.get(key, empty)))
    write_csv(categories, OUT / "categories_funnel.csv")

    causes = []
    for key in sorted(by_cause, key=lambda k: (int(k[1:].split(".")[0]), int(k.split(".S")[1]))):
        causes.append(funnel_row(key, names.get(key, ""), by_cause[key]))
    write_csv(causes, OUT / "root_causes_funnel.csv")

    reason_rows = []                                    # most frequent reasons first
    for (cause, outcome, why), times in sorted(reasons.items(), key=lambda item: (item[0][0], -item[1])):
        reason_rows.append({"root_cause": cause, "outcome": outcome, "times": times, "why": why})
    write_csv(reason_rows, OUT / "root_causes_reasons.csv")

    summary = {"smells": 0, "submitted": 0, "measured": 0, "confirmed": 0}
    for row in categories:
        for field in summary:
            summary[field] = summary[field] + row[field]
    summary["confirmed_per_100_smells"] = percent(summary["confirmed"], summary["smells"])
    savings = []                                        # every confirmed repair of the 12 runs
    for counts in by_category.values():
        savings.extend(counts["savings"])
    summary["median_saving_pct"] = round(median(savings), 1)
    summary["categories_with_a_smell"] = sum(1 for row in categories if row["smells"] > 0)
    summary["categories_with_a_confirmed_repair"] = sum(1 for row in categories if row["confirmed"] > 0)
    summary["root_causes_with_a_smell"] = len(causes)
    summary["root_causes_with_a_confirmed_repair"] = sum(1 for row in causes if row["confirmed"] > 0)
    write_json(summary, OUT / "categories_summary.json")
    print("wrote", OUT / "categories_*", "and", OUT / "root_causes_funnel.csv")


if __name__ == "__main__":
    main()
