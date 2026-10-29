"""RQ1, Step 1 (Find): what each run listed as possibly wasteful.

Reads, for each of the 18 runs:
  record/steps/step1.jsonl   the step-1 file as the step keeper locked it. One line
                             per unit, with its suspicions; each suspicion has the
                             lines, why, and (in the two taxonomy skills) a root_cause
  rules.json                 the static rules' report on the untouched repository.
                             It is the same in every skill; only Taxonomy+Rules
                             showed it to the agent (through scan.py)
  record/scans.jsonl         each time the agent ran scan.py (Taxonomy+Rules only),
                             with the flagged units not on its list at that moment
  record/events.jsonl        when the agent finished step 1

Writes to analysis/output/rq1/:
  step1_per_run.csv          one row per run
  step1_models_<metric>.csv  Sonnet vs Haiku in each (repo, skill) cell
  step1_skills_<metric>.csv  the three skills in each (repo, model) cell
  step1_repos_<metric>.csv   the three repositories in each (skill, model) cell
  step1_overlap.csv          how far the six runs on one repository listed the same units
  step1_summary.json         the counts behind the comparisons

Run:  python3 analysis/rq1_step1.py
"""

from common import (MODEL_NAMES, MODELS, OUTPUT_DIR, REPOS, SKILL_NAMES, SKILLS,
                    all_runs, category_of, file_of, is_test, percent, read_json,
                    read_jsonl, repo_sizes, run_folder, write_csv, write_json)
from compare import (compare_models, compare_repos, compare_skills,
                     count_highest, count_model_wins, count_skill_orders)

OUT = OUTPUT_DIR / "rq1"   # where this script writes


def listed_units(repo, skill, model):
    """The set of units one run listed in step 1."""
    path = run_folder(repo, skill, model) / "record" / "steps" / "step1.jsonl"
    units = set()                                       # a set keeps each unit once
    for record in read_jsonl(path):                     # one record per listed unit
        units.add(record["unit"])
    return units


def rule_flagged_units(repo, skill, model):
    """The set of units that at least one static rule flags, from rules.json."""
    rules = read_json(run_folder(repo, skill, model) / "rules.json")
    units = set()
    for entry in rules["units"]:                        # one entry per flagged unit
        units.add(entry["unit"])
    return units


def scan_added_units(repo, skill, model):
    """Units the agent listed after scan.py showed them as missing (Taxonomy+Rules only).

    Read from the raw files, without meta.json:
      record/scans.jsonl   one line per time the agent ran scan.py. Its "not_listed"
                           holds the units a rule flags that were NOT on the agent's
                           list at that moment. "t" is when it ran.
      record/events.jsonl  the step keeper's events; the "done" line of step 1 says
                           when the agent finished its list.
      record/steps/step1.jsonl   the final list.

    A unit counts as added when (1) a scan run before step 1 was finished showed
    it as not on the list, and (2) it is on the final list. The files cannot show
    whether the agent listed it because of the scan or from its own reading.
    """
    folder = run_folder(repo, skill, model)

    # When did the agent finish step 1?
    done1_time = None
    for event in read_jsonl(folder / "record" / "events.jsonl"):
        if event.get("event") == "done" and event.get("step") == 1:
            done1_time = event["t"]

    # Units that some scan before that moment showed as not on the list
    shown_missing = set()
    scans_file = folder / "record" / "scans.jsonl"
    if scans_file.exists():                             # only Taxonomy+Rules has scans
        for scan in read_jsonl(scans_file):
            if done1_time is not None and scan["t"] > done1_time:
                continue                                # a scan after step 1 cannot add to it
            for unit in scan.get("not_listed") or []:
                shown_missing.add(unit)

    # Of those, the ones on the final list
    return shown_missing & listed_units(repo, skill, model)


def step1_of(repo, skill, model, sizes):
    """All Step-1 numbers of one run, as a dictionary."""
    path = run_folder(repo, skill, model) / "record" / "steps" / "step1.jsonl"
    records = read_jsonl(path)                          # one record per listed unit

    units = set()                                       # the listed units
    files = set()                                       # the files they are in
    test_units = set()                                  # listed units that are in test files
    suspicions = 0                                      # how many suspicions in total
    causes = set()                                      # root causes suspected (taxonomy skills)
    for record in records:
        unit = record["unit"]
        units.add(unit)
        files.add(file_of(unit))
        if is_test(file_of(unit)):
            test_units.add(unit)
        for suspicion in record["suspicions"]:
            suspicions = suspicions + 1
            if suspicion.get("root_cause"):             # missing in Unguided
                causes.add(suspicion["root_cause"])

    categories = set()                                  # C10.S4 -> C10
    for cause in causes:
        categories.add(category_of(cause))

    flagged = rule_flagged_units(repo, skill, model)    # units a rule flags
    both = units & flagged                              # listed by the agent AND flagged by a rule

    row = {}
    row["repo"] = repo
    row["skill"] = SKILL_NAMES[skill]
    row["model"] = MODEL_NAMES[model]
    row["units_listed"] = len(units)
    row["pct_of_repo_units"] = percent(len(units), sizes[repo]["units"])
    row["suspicions"] = suspicions
    row["files_with_a_listed_unit"] = len(files)
    row["pct_of_repo_files"] = percent(len(files), sizes[repo]["files"])
    row["test_units_listed"] = len(test_units)
    # Unguided has no taxonomy: write None (an empty cell), not 0
    if skill == "control":
        row["root_causes_suspected"] = None
        row["categories_suspected"] = None
    else:
        row["root_causes_suspected"] = len(causes)
        row["categories_suspected"] = len(categories)
    row["units_flagged_by_rules_in_repo"] = len(flagged)
    row["listed_units_flagged_by_rules"] = len(both)
    row["pct_listed_flagged_by_rules"] = percent(len(both), len(units))   # of what the agent listed
    row["pct_rule_units_listed"] = percent(len(both), len(flagged))       # of what the rules flag
    if skill == "full":                                 # scan.py exists only in Taxonomy+Rules
        row["scan_units_added"] = len(scan_added_units(repo, skill, model))
    else:
        row["scan_units_added"] = None
    return row


def jaccard(a, b):
    """Units in both sets / units in either set, as a percentage (0 = nothing shared)."""
    shared = a & b                                      # in both
    either = a | b                                      # in at least one
    return percent(len(shared), len(either))


def overlap_rows():
    """For each repository: how much the six runs agree on which units to list."""
    rows = []                                           # the table we build
    for repo in REPOS:
        # The units of each of the six runs on this repository
        sets = {}
        for skill in SKILLS:
            for model in MODELS:
                sets[(skill, model)] = listed_units(repo, skill, model)

        # How many of the six runs listed each unit
        times_listed = {}                               # {unit: number of runs}
        for units in sets.values():
            for unit in units:
                times_listed[unit] = times_listed.get(unit, 0) + 1

        in_any = len(times_listed)                      # listed by at least one run
        in_all = 0                                      # listed by all six runs
        in_one = 0                                      # listed by exactly one run
        for count in times_listed.values():
            if count == 6:
                in_all = in_all + 1
            if count == 1:
                in_one = in_one + 1

        row = {}
        row["repo"] = repo
        row["units_listed_by_any_run"] = in_any
        row["units_listed_by_all_6_runs"] = in_all
        row["units_listed_by_only_1_run"] = in_one
        # Sonnet and Haiku with the same skill: how similar are their lists?
        for skill in SKILLS:
            column = "jaccard_sonnet_haiku_" + SKILL_NAMES[skill]
            row[column] = jaccard(sets[(skill, "sonnet")], sets[(skill, "haiku")])
        rows.append(row)
    return rows


def main():
    sizes = repo_sizes()                                # units and files per repository

    per_run = {}                                        # {(repo, skill, model): numbers of that run}
    for repo, skill, model in all_runs():               # the 18 runs
        per_run[(repo, skill, model)] = step1_of(repo, skill, model, sizes)
    write_csv(list(per_run.values()), OUT / "step1_per_run.csv")

    summary = {}                                        # the counts the text cites
    metrics = ["units_listed", "suspicions", "pct_listed_flagged_by_rules", "pct_rule_units_listed"]
    for metric in metrics:
        models = compare_models(per_run, metric)        # Sonnet vs Haiku
        skills = compare_skills(per_run, metric)        # the three skills
        repos = compare_repos(per_run, metric)          # the three repositories
        write_csv(models, OUT / ("step1_models_" + metric + ".csv"))
        write_csv(skills, OUT / ("step1_skills_" + metric + ".csv"))
        write_csv(repos, OUT / ("step1_repos_" + metric + ".csv"))
        summary[metric] = {"model_wins": count_model_wins(models),
                           "skill_order": count_skill_orders(skills),
                           "skill_highest": count_highest(skills)}

    overlap = overlap_rows()                            # agreement between the runs
    write_csv(overlap, OUT / "step1_overlap.csv")
    summary["overlap"] = overlap
    write_json(summary, OUT / "step1_summary.json")
    print("wrote", OUT / "step1_*")


if __name__ == "__main__":
    main()
