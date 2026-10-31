"""RQ1, all six runs on a repository together: how far the runs complement each other.

For each repository, the six runs (3 skills x 2 models) are put together:

  units               functions and methods in the repository (repo_stats.tsv)
  listed_any          units at least one run listed in step 1
  smelly_any          units at least one run found smelly in step 2
  smelly_2_or_more    units two or more of the six runs found smelly
  smelly_all_6        units all six runs found smelly
  confirmed_any       functions with a confirmed repair (or partial) in at least one run
  by_1_skill ...      of those, how many were confirmed by exactly one, two or all
                      three skills (with either model)
  only_<skill>        confirmed by that skill alone
  by_1_model          confirmed with only one of the two models
  median_best_saving  for each confirmed function its largest saving over the runs;
                      the median of those

Reads the same files as rq1_step1.py, rq1_step2.py and rq1_step3.py, through
their functions, so every count here means what it means there.

Writes to analysis/output/rq1/:
  together_per_repo.csv   one row per repository

Run:  python3 analysis/rq1_together.py
"""

from common import (MODELS, OUTPUT_DIR, REPOS, SAVES, SKILL_NAMES, SKILLS, median, percent,
                    repo_sizes, write_csv)
from rq1_step1 import listed_units
from rq1_step2 import smells_of
from rq1_step3 import review_of

OUT = OUTPUT_DIR / "rq1"   # where this script writes


def together_row(repo, sizes):
    """The numbers of one repository, all six runs together."""
    listed = set()                                      # listed by any run
    times_smelly = {}                                   # {unit: runs that found it smelly}
    confirmed_by_skill = {}                             # {skill: functions it confirmed}
    confirmed_by_model = {}                             # {model: functions it confirmed}
    confirmed = set()                                   # functions with a confirmed repair
    best_saving = {}                                    # {function: its largest saving}
    for skill in SKILLS:
        confirmed_by_skill[skill] = set()
    for model in MODELS:
        confirmed_by_model[model] = set()

    for skill in SKILLS:
        for model in MODELS:
            listed = listed | listed_units(repo, skill, model)

            smelly = set()                              # smelly units of this run
            for smell in smells_of(repo, skill, model):
                smelly.add(smell["unit"])
            for unit in smelly:
                times_smelly[unit] = times_smelly.get(unit, 0) + 1

            for repair in review_of(repo, skill, model):
                if repair["status"] not in SAVES:
                    continue                            # only confirmed (or partial) repairs
                unit = repair["unit"]
                confirmed.add(unit)
                confirmed_by_skill[skill].add(unit)
                confirmed_by_model[model].add(unit)
                saving = repair["mean_saving_pct"]
                if unit not in best_saving or saving > best_saving[unit]:
                    best_saving[unit] = saving

    smelly_2_or_more = 0
    smelly_all_6 = 0
    for count in times_smelly.values():
        if count >= 2:
            smelly_2_or_more = smelly_2_or_more + 1
        if count == 6:
            smelly_all_6 = smelly_all_6 + 1

    # For each confirmed function: how many skills, and how many models, confirmed it
    by_skills = {1: 0, 2: 0, 3: 0}                      # {number of skills: functions}
    only = {}                                           # {skill: functions only it confirmed}
    for skill in SKILLS:
        only[skill] = 0
    by_1_model = 0
    for unit in confirmed:                              # every confirmed function
        skills_with_it = []
        for skill in SKILLS:
            if unit in confirmed_by_skill[skill]:
                skills_with_it.append(skill)
        by_skills[len(skills_with_it)] += 1
        if len(skills_with_it) == 1:
            only[skills_with_it[0]] += 1
        models_with_it = 0
        for model in MODELS:
            if unit in confirmed_by_model[model]:
                models_with_it = models_with_it + 1
        if models_with_it == 1:
            by_1_model = by_1_model + 1

    row = {}
    row["repo"] = repo
    row["units"] = sizes[repo]["units"]
    row["listed_any"] = len(listed)
    row["smelly_any"] = len(times_smelly)
    row["pct_smelly_any"] = percent(len(times_smelly), sizes[repo]["units"])
    row["smelly_2_or_more"] = smelly_2_or_more
    row["smelly_all_6"] = smelly_all_6
    row["confirmed_any"] = len(confirmed)
    row["by_1_skill"] = by_skills[1]
    row["by_2_skills"] = by_skills[2]
    row["by_3_skills"] = by_skills[3]
    for skill in SKILLS:
        row["only_" + SKILL_NAMES[skill]] = only[skill]
    row["by_1_model"] = by_1_model
    row["median_best_saving_pct"] = round(median(list(best_saving.values())), 1)
    return row


def main():
    sizes = repo_sizes()
    rows = []
    for repo in REPOS:
        rows.append(together_row(repo, sizes))
    write_csv(rows, OUT / "together_per_repo.csv")
    print("wrote", OUT / "together_per_repo.csv")


if __name__ == "__main__":
    main()
