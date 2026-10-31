"""RQ1, why Unguided's confirmed repairs have the highest median saving with Sonnet.

The question: in the table of runs, Unguided with Sonnet has the highest median
saving on every repository. Is that because the taxonomy configurations make
worse or smaller repairs, or because they repair different units?

Reads analysis/output/rq1/repairs_per_repair.csv (written by rq1_repairs.py:
one row per measured repair, with our verdict, saving, lines changed and change
group), and each run's step-1 and step-2 files through rq1_step1.py and
rq1_step2.py.

Compares, with the repository and the model fixed:

  1. per run, how the savings are spread: confirmed repairs below 10%, from 10
     to 50%, and 50% or more, and the regressions
  2. units that Unguided and a taxonomy run BOTH measured: the best saving each
     reached on that unit (a "pair"). If the taxonomy made worse repairs, its
     savings would be lower on the same units.
  3. units a taxonomy run measured that Unguided did NOT: their savings, and
     what Unguided did with them in Steps 1 and 2 (never listed, listed and
     rejected, or accepted as smelly but not measured)

Writes to analysis/output/rq1/:
  unguided_per_run.csv       spread of the savings, per run
  unguided_pairs.csv         one row per pair: a unit measured by Unguided and by one
                             taxonomy run (a unit both taxonomy runs measured gives two)
  unguided_own_units.csv     per taxonomy run: repairs on shared units and on its own units
  unguided_repair_shape.csv  per model and skill: lines changed and change to the loops
  unguided_summary.json      the totals the answer uses. Repairs are added up over the
                             runs; units count once, as distinct (repository, unit)

Run after rq1_repairs.py:  python3 analysis/rq1_unguided_savings.py
"""

import csv

from common import (MODEL_NAMES, MODELS, OUTPUT_DIR, REPOS, SKILL_NAMES, median, write_csv,
                    write_json)
from rq1_step1 import listed_units
from rq1_step2 import smells_of

OUT = OUTPUT_DIR / "rq1"   # where this script writes
TAXONOMY_SKILLS = ["full", "knowledge"]                 # the two configurations with a taxonomy


def read_repairs():
    """The measured repairs from repairs_per_repair.csv, with numbers turned into numbers."""
    repairs = []
    with open(OUT / "repairs_per_repair.csv") as handle:
        for row in csv.DictReader(handle):
            row["saving"] = float(row["saving_pct"]) if row["saving_pct"] else None   # None: not used
            row["confirmed"] = row["confirmed"] == "True"   # confirmed or partial
            repairs.append(row)
    return repairs


def of_run(repairs, repo, skill, model):
    """The repairs of one run."""
    kept = []
    for row in repairs:
        if row["repo"] == repo and row["skill"] == SKILL_NAMES[skill] and row["model"] == MODEL_NAMES[model]:
            kept.append(row)
    return kept


def spread(rows):
    """How the savings of a group of repairs are spread, as a dictionary."""
    savings = []                                        # savings of the confirmed repairs
    regressed = []                                      # savings of the regressed ones (negative)
    for row in rows:
        if row["confirmed"]:
            savings.append(row["saving"])
        if row["verdict"] == "regressed":
            regressed.append(row["saving"])
    result = {"measured": len(rows), "confirmed": len(savings)}
    result["below_10pct"] = len([s for s in savings if s < 10])
    result["10_to_50pct"] = len([s for s in savings if 10 <= s < 50])
    result["50pct_or_more"] = len([s for s in savings if s >= 50])
    result["median_saving_pct"] = round(median(savings), 1) if savings else None
    result["regressed"] = len(regressed)
    result["worst_regression_pct"] = round(min(regressed), 1) if regressed else None
    return result


def best_saving(rows, unit):
    """The largest saving any repair of `unit` reached among `rows` (any verdict);
    None when none of them has a saving (see excluded_repairs.csv)."""
    best = None
    for row in rows:
        if row["unit"] != unit or row["saving"] is None:
            continue
        if best is None or row["saving"] > best:
            best = row["saving"]
    return best


def main():
    repairs = read_repairs()

    # 1. Spread of the savings, per run
    per_run = []
    for model in MODELS:
        for repo in REPOS:
            for skill in ["full", "knowledge", "control"]:
                line = {"model": MODEL_NAMES[model], "repo": repo, "skill": SKILL_NAMES[skill]}
                line.update(spread(of_run(repairs, repo, skill, model)))
                per_run.append(line)
    write_csv(per_run, OUT / "unguided_per_run.csv")

    pairs = []                                          # 2. the same unit on both sides
    own = []                                            # 3. units only the taxonomy run measured
    fate_of_unit = {}                                   # {(model, repo, unit): what Unguided did with it}
    for model in MODELS:
        for repo in REPOS:
            unguided = of_run(repairs, repo, "control", model)
            unguided_units = set()
            for row in unguided:
                unguided_units.add(row["unit"])
            listed = listed_units(repo, "control", model)          # Unguided's step-1 list
            smelly = set()                                         # Unguided's smelly units
            for smell in smells_of(repo, "control", model):
                smelly.add(smell["unit"])

            for skill in TAXONOMY_SKILLS:
                taxonomy = of_run(repairs, repo, skill, model)
                shared_rows = []                        # repairs on units Unguided also measured
                own_rows = []                           # repairs on units Unguided did not measure
                for row in taxonomy:
                    if row["unit"] in unguided_units:
                        shared_rows.append(row)
                    else:
                        own_rows.append(row)

                # 2. One pair per shared unit: the best saving on each side
                shared_units = set()
                for row in shared_rows:
                    shared_units.add(row["unit"])
                for unit in sorted(shared_units):
                    causes = sorted({row["root_cause"] for row in shared_rows if row["unit"] == unit})
                    u = best_saving(unguided, unit)
                    t = best_saving(shared_rows, unit)
                    if u is None or t is None:          # one side has no saving to compare
                        continue
                    pairs.append({"model": MODEL_NAMES[model], "repo": repo, "skill": SKILL_NAMES[skill],
                                  "unit": unit, "unguided_saving_pct": u, "taxonomy_saving_pct": t,
                                  "difference_points": round(u - t, 1),
                                  "taxonomy_root_causes": " ".join(causes)})

                # 3. What Unguided did with the units only the taxonomy run measured
                fate = {"never listed": 0, "listed, rejected": 0, "smelly, not measured": 0}
                small_causes = {}                       # root causes of own confirmed repairs below 10%
                for unit in {row["unit"] for row in own_rows}:
                    if unit in smelly:
                        where = "smelly, not measured"
                    elif unit in listed:
                        where = "listed, rejected"
                    else:
                        where = "never listed"
                    fate[where] += 1
                    fate_of_unit[(MODEL_NAMES[model], repo, unit)] = where   # the same for both taxonomy runs
                for row in own_rows:
                    if row["confirmed"] and row["saving"] < 10:
                        small_causes[row["root_cause"]] = small_causes.get(row["root_cause"], 0) + 1

                line = {"model": MODEL_NAMES[model], "repo": repo, "skill": SKILL_NAMES[skill]}
                shared = spread(shared_rows)
                mine = spread(own_rows)
                line["shared_repairs"] = shared["measured"]
                line["shared_confirmed"] = shared["confirmed"]
                line["shared_median_pct"] = shared["median_saving_pct"]
                line["own_repairs"] = mine["measured"]
                line["own_confirmed"] = mine["confirmed"]
                line["own_median_pct"] = mine["median_saving_pct"]
                line["own_confirmed_below_10pct"] = mine["below_10pct"]
                line["own_units_unguided_never_listed"] = fate["never listed"]
                line["own_units_unguided_listed_rejected"] = fate["listed, rejected"]
                line["own_units_unguided_smelly_not_measured"] = fate["smelly, not measured"]
                line["root_causes_of_own_below_10pct"] = " ".join(
                    f"{cause}:{count}" for cause, count in sorted(small_causes.items()))
                own.append(line)
    # Size and kind of the repairs, per model and skill (columns of repairs_per_repair.csv)
    shape = []
    for model in MODELS:
        for skill in ["full", "knowledge", "control"]:
            rows = [r for r in repairs if r["model"] == MODEL_NAMES[model] and r["skill"] == SKILL_NAMES[skill]]
            line = {"model": MODEL_NAMES[model], "skill": SKILL_NAMES[skill], "measured": len(rows)}
            line["median_lines_changed"] = median([int(r["lines_changed"]) for r in rows])
            line["repairs_1_2_lines"] = len([r for r in rows if r["size_group"] == "1-2"])
            for group in ["Changes the loops", "Fewer calls inside loops",
                          "Fewer calls outside loops", "Same loops and calls"]:
                line[group] = len([r for r in rows if r["change_group"] == group])
            shape.append(line)
    write_csv(shape, OUT / "unguided_repair_shape.csv")

    write_csv(pairs, OUT / "unguided_pairs.csv")
    write_csv(own, OUT / "unguided_own_units.csv")

    # Totals per model: the spread pooled over repositories, the pairs, the own units
    summary = {}
    for model in MODELS:
        name = MODEL_NAMES[model]
        part = {}
        for skill in ["full", "knowledge", "control"]:
            rows = [r for r in repairs if r["model"] == name and r["skill"] == SKILL_NAMES[skill]]
            part[SKILL_NAMES[skill]] = spread(rows)
        differences = [p["difference_points"] for p in pairs if p["model"] == name]
        part["taxonomy_measured_repairs"] = (part[SKILL_NAMES["full"]]["measured"]
                                             + part[SKILL_NAMES["knowledge"]]["measured"])
        # A unit both taxonomy runs measured gives two pairs, but counts once as a unit
        part["pairs"] = {
            "pairs": len(differences),
            "distinct_units": len({(p["repo"], p["unit"]) for p in pairs if p["model"] == name}),
            "unguided_higher_by_more_than_5_points": len([d for d in differences if d > 5]),
            "within_5_points": len([d for d in differences if -5 <= d <= 5]),
            "taxonomy_higher_by_more_than_5_points": len([d for d in differences if d < -5]),
            "median_difference_points": median(differences),
        }
        # Repairs are added up over the runs; units count once, even when both taxonomy runs measured them
        own_rows = [o for o in own if o["model"] == name]
        fates = [where for (m, repo, unit), where in fate_of_unit.items() if m == name]
        part["own_units"] = {
            "own_repairs": sum(o["own_repairs"] for o in own_rows),
            "own_confirmed_below_10pct": sum(o["own_confirmed_below_10pct"] for o in own_rows),
            "own_units": len(fates),
            "units_unguided_never_listed": fates.count("never listed"),
            "units_unguided_listed_rejected": fates.count("listed, rejected"),
            "units_unguided_smelly_not_measured": fates.count("smelly, not measured"),
        }
        summary[name] = part
    write_json(summary, OUT / "unguided_summary.json")
    print("wrote", OUT / "unguided_*")


if __name__ == "__main__":
    main()
