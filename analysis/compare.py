"""The three comparisons every step of RQ1 makes, with the other factors held fixed.

All functions take `per_run`, a dictionary whose keys are (repo, skill, model)
and whose values are the numbers of that run, e.g.

    per_run[("dx-toolkit", "full", "sonnet")]["units_listed"] == 244

and the name of one number (the "metric"). They return a list of rows (one
dictionary per row), ready to be written with write_csv().

  compare_models   Sonnet against Haiku, in each of the 9 (repo, skill) cells
  compare_skills   the three skills, in each of the 6 (repo, model) cells
  compare_repos    the three repositories, in each of the 6 (skill, model) cells
"""

from common import MODEL_NAMES, MODELS, REPOS, SKILL_NAMES, SKILLS


def compare_models(per_run, metric):
    """One row per (repo, skill): the metric for Sonnet and for Haiku, and which is higher."""
    rows = []                                           # the table we build
    for repo in REPOS:                                  # each repository
        for skill in SKILLS:                            # each skill
            sonnet = per_run[(repo, skill, "sonnet")][metric]   # the value for Sonnet
            haiku = per_run[(repo, skill, "haiku")][metric]     # the value for Haiku

            # Decide which model has the higher value
            if sonnet is None or haiku is None:         # e.g. root causes in Unguided
                higher = "n/a"
            elif sonnet > haiku:
                higher = "Sonnet"
            elif haiku > sonnet:
                higher = "Haiku"
            else:
                higher = "tie"

            row = {}                                    # one row of the table
            row["repo"] = repo
            row["skill"] = SKILL_NAMES[skill]
            row["Sonnet"] = sonnet
            row["Haiku"] = haiku
            row["higher"] = higher
            rows.append(row)
    return rows


def compare_skills(per_run, metric):
    """One row per (repo, model): the metric for each of the three skills."""
    rows = []                                           # the table we build
    for repo in REPOS:                                  # each repository
        for model in MODELS:                            # each model
            row = {}                                    # one row of the table
            row["repo"] = repo
            row["model"] = MODEL_NAMES[model]
            for skill in SKILLS:                        # one column per skill
                row[SKILL_NAMES[skill]] = per_run[(repo, skill, model)][metric]
            row["highest"] = highest_skill(row)         # which skill has the largest value
            rows.append(row)
    return rows


def highest_skill(row):
    """The name of the skill with the largest value in one compare_skills() row.

    Several names joined by " = " when they share the largest value.
    """
    best_value = None                                   # the largest value seen so far
    best_names = []                                     # the skills that have it
    for skill in SKILLS:                                # look at each skill's column
        name = SKILL_NAMES[skill]
        value = row[name]
        if value is None:                               # this skill has no value here
            continue
        if best_value is None or value > best_value:    # a new largest value
            best_value = value
            best_names = [name]
        elif value == best_value:                       # the same as the largest: a tie
            best_names.append(name)
    return " = ".join(best_names)


def compare_repos(per_run, metric):
    """One row per (skill, model): the metric for each of the three repositories."""
    rows = []                                           # the table we build
    for skill in SKILLS:                                # each skill
        for model in MODELS:                            # each model
            row = {}                                    # one row of the table
            row["skill"] = SKILL_NAMES[skill]
            row["model"] = MODEL_NAMES[model]
            for repo in REPOS:                          # one column per repository
                row[repo] = per_run[(repo, skill, model)][metric]
            rows.append(row)
    return rows


def count_model_wins(rows):
    """How often each model had the higher value, from compare_models() rows."""
    counts = {"Sonnet": 0, "Haiku": 0, "tie": 0, "n/a": 0}   # start every count at 0
    for row in rows:                                    # each (repo, skill) cell
        winner = row["higher"]                          # "Sonnet", "Haiku", "tie" or "n/a"
        counts[winner] = counts[winner] + 1             # add one to that count
    return counts


def count_highest(rows):
    """How often each skill has the largest value, from compare_skills() rows.

    A tie counts for every skill that shares the largest value.
    """
    counts = {}                                         # {skill name: cells where it is highest}
    for skill in SKILLS:
        counts[SKILL_NAMES[skill]] = 0                  # start every count at 0
    for row in rows:                                    # each (repo, model) cell
        if row["highest"] == "":                        # no skill has a value (e.g. root causes)
            continue
        for name in row["highest"].split(" = "):        # one name, or several when tied
            counts[name] = counts[name] + 1
    return counts


def count_skill_orders(rows):
    """How often the expected order of the skills holds, from compare_skills() rows.

    Expected: Taxonomy+Rules >= Taxonomy >= Unguided. Also counts the weaker
    claim Taxonomy+Rules >= Unguided, which leaves Taxonomy out.
    """
    cells = 0                                           # cells where all three skills have a value
    full_order = 0                                      # cells where the whole order holds
    full_over_unguided = 0                              # cells where Taxonomy+Rules >= Unguided
    for row in rows:                                    # each (repo, model) cell
        rules = row["Taxonomy+Rules"]
        taxonomy = row["Taxonomy"]
        unguided = row["Unguided"]
        if rules is None or taxonomy is None or unguided is None:
            continue                                    # a metric Unguided does not have
        cells = cells + 1
        if rules >= taxonomy and taxonomy >= unguided:
            full_order = full_order + 1
        if rules >= unguided:
            full_over_unguided = full_over_unguided + 1
    return {"cells": cells,
            "full>=knowledge>=control": full_order,
            "full>=control": full_over_unguided}
