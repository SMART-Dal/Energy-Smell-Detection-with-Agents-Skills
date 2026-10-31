"""RQ2: how far two runs agree on what is smelly and on its root cause.

Only the taxonomy runs label root causes, so the comparisons are between the four
taxonomy runs of each repository, in pairs:
  models           Sonnet vs Haiku, with the same skill (Taxonomy+Rules, then Taxonomy)
  configurations   Taxonomy+Rules vs Taxonomy, with the same model (Sonnet, then Haiku)
  any two runs     all six pairs of the four runs, for reference

For each pair, on one repository:
  units     the smelly units of each run (a unit with at least one accepted smell)
  instances the (unit, root cause) pairs of each run
  same root cause / same category: among the units BOTH runs found smelly, how
            many got at least one root cause (or category) in common

Agreement on a set is the Jaccard index: in both / in either. The counts are
added up over the three repositories before the shares are taken.

Writes to analysis/output/rq2/:
  agreement.csv        one row per comparison, the three repositories together
  agreement_by_repo.csv one row per comparison and repository

Run:  python3 analysis/rq2_agreement.py
"""

from itertools import combinations

from common import (MODEL_NAMES, OUTPUT_DIR, REPOS, SKILL_NAMES, category_of, percent,
                    write_csv)
from rq1_step2 import smells_of

OUT = OUTPUT_DIR / "rq2"   # where this script writes
RUNS = [("full", "sonnet"), ("full", "haiku"), ("knowledge", "sonnet"), ("knowledge", "haiku")]

# The comparisons: (name, list of run pairs)
COMPARISONS = [
    ("Sonnet vs Haiku, Taxonomy+Rules", [(("full", "sonnet"), ("full", "haiku"))]),
    ("Sonnet vs Haiku, Taxonomy", [(("knowledge", "sonnet"), ("knowledge", "haiku"))]),
    ("Taxonomy+Rules vs Taxonomy, Sonnet", [(("full", "sonnet"), ("knowledge", "sonnet"))]),
    ("Taxonomy+Rules vs Taxonomy, Haiku", [(("full", "haiku"), ("knowledge", "haiku"))]),
    ("Any two taxonomy runs", list(combinations(RUNS, 2))),
]


def root_causes_by_unit(repo, skill, model):
    """{unit: set of root causes} for the accepted smells of one run."""
    found = {}
    for smell in smells_of(repo, skill, model):
        if smell.get("root_cause"):
            found.setdefault(smell["unit"], set()).add(smell["root_cause"])
    return found


def compare(a, b):
    """Counts for two runs on one repository; a and b are {unit: set of root causes}."""
    instances_a = {(u, c) for u, causes in a.items() for c in causes}
    instances_b = {(u, c) for u, causes in b.items() for c in causes}
    both_units = set(a) & set(b)
    same_cause = 0
    same_category = 0
    for unit in both_units:
        if a[unit] & b[unit]:
            same_cause = same_cause + 1
        if {category_of(c) for c in a[unit]} & {category_of(c) for c in b[unit]}:
            same_category = same_category + 1
    return {"units_both": len(both_units), "units_either": len(set(a) | set(b)),
            "instances_both": len(instances_a & instances_b),
            "instances_either": len(instances_a | instances_b),
            "same_root_cause": same_cause, "same_category": same_category}


def shares(counts):
    """The agreement shares from added-up counts."""
    return {"units_jaccard_pct": percent(counts["units_both"], counts["units_either"]),
            "instances_jaccard_pct": percent(counts["instances_both"], counts["instances_either"]),
            "pct_same_root_cause": percent(counts["same_root_cause"], counts["units_both"]),
            "pct_same_category": percent(counts["same_category"], counts["units_both"])}


def main():
    labels = {}
    for repo in REPOS:
        for skill, model in RUNS:
            labels[(repo, skill, model)] = root_causes_by_unit(repo, skill, model)

    pooled_rows = []
    repo_rows = []
    for name, pairs in COMPARISONS:
        total = {"units_both": 0, "units_either": 0, "instances_both": 0,
                 "instances_either": 0, "same_root_cause": 0, "same_category": 0}
        for repo in REPOS:
            for first, second in pairs:
                counts = compare(labels[(repo,) + first], labels[(repo,) + second])
                for key in total:
                    total[key] = total[key] + counts[key]
                if len(pairs) == 1:                     # one row per repository for single pairs
                    line = {"comparison": name, "repo": repo}
                    line.update(counts)
                    line.update(shares(counts))
                    repo_rows.append(line)
        line = {"comparison": name, "pairs_per_repo": len(pairs)}
        line.update(total)
        line.update(shares(total))
        pooled_rows.append(line)
    write_csv(pooled_rows, OUT / "agreement.csv")
    write_csv(repo_rows, OUT / "agreement_by_repo.csv")
    print("wrote", OUT / "agreement.csv")


if __name__ == "__main__":
    main()
