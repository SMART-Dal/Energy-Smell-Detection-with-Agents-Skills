"""RQ1, Step 2 (Decide): which suspicions each run accepted as energy smells.

Reads, for each of the 18 runs:
  record/steps/step1.jsonl   the suspicions, with the root cause first suspected
  record/steps/step2.jsonl   one line per unit, with one decision per suspicion:
                             verdict "accepted" or "rejected", and (in the two
                             taxonomy skills) a root_cause
  rules.json                 the static rules' report on the untouched repository

An accepted suspicion is what the paper calls a smell; a unit with at least one
smell is a smelly unit.

Writes to analysis/output/rq1/:
  step2_per_run.csv            one row per run
  step2_models_<metric>.csv    Sonnet vs Haiku in each (repo, skill) cell
  step2_skills_<metric>.csv    the three skills in each (repo, model) cell
  step2_repos_<metric>.csv     the three repositories in each (skill, model) cell
  step2_union.csv              smelly units per repository, over all six runs
  step2_categories.csv         smells per category, in the two taxonomy skills
  step2_rules_agreement_full_vs_knowledge.csv
                               smells whose root cause a rule also names, by skill
  step2_summary.json           the counts behind the comparisons

Run:  python3 analysis/rq1_step2.py
"""

from common import (MODEL_NAMES, MODELS, OUTPUT_DIR, REPOS, SKILL_NAMES, SKILLS,
                    all_runs, category_of, file_of, is_test, percent, read_json,
                    read_jsonl, repo_sizes, run_folder, write_csv, write_json)
from compare import (compare_models, compare_repos, compare_skills,
                     count_highest, count_model_wins, count_skill_orders)

OUT = OUTPUT_DIR / "rq1"   # where this script writes


def decisions_of(repo, skill, model):
    """Every step-2 decision of one run. Each decision also gets the name of its unit."""
    path = run_folder(repo, skill, model) / "record" / "steps" / "step2.jsonl"
    decisions = []
    for record in read_jsonl(path):                     # one record per unit
        for decision in record["decisions"]:            # one decision per suspicion
            decision["unit"] = record["unit"]           # remember which unit it belongs to
            decisions.append(decision)
    return decisions


def smells_of(repo, skill, model):
    """Only the accepted decisions (the smells) of one run."""
    smells = []
    for decision in decisions_of(repo, skill, model):
        if decision["verdict"] == "accepted":
            smells.append(decision)
    return smells


def step1_root_causes(repo, skill, model):
    """The root cause each suspicion had in step 1, keyed by (unit, label)."""
    path = run_folder(repo, skill, model) / "record" / "steps" / "step1.jsonl"
    causes = {}
    for record in read_jsonl(path):
        for suspicion in record["suspicions"]:
            causes[(record["unit"], suspicion["label"])] = suspicion.get("root_cause")
    return causes


def rule_root_causes(repo, skill, model):
    """For each unit a rule flags: the root causes the rules name for it."""
    rules = read_json(run_folder(repo, skill, model) / "rules.json")
    named = {}                                          # {unit: set of root causes}
    for entry in rules["units"]:                        # one entry per flagged unit
        causes = set()
        for candidate in entry.get("candidates") or []:
            causes.add(candidate["id"])
        named[entry["unit"]] = causes
    return named


def step2_of(repo, skill, model, sizes):
    """All Step-2 numbers of one run, as a dictionary."""
    decisions = decisions_of(repo, skill, model)
    smells = smells_of(repo, skill, model)
    taxonomy = skill != "control"                       # Unguided has no root causes

    smelly_units = set()                                # units with at least one smell
    smelly_non_test = set()                             # the same, leaving test files out
    causes = set()                                      # root causes of the smells
    for smell in smells:
        smelly_units.add(smell["unit"])
        if not is_test(file_of(smell["unit"])):
            smelly_non_test.add(smell["unit"])
        if smell.get("root_cause"):
            causes.add(smell["root_cause"])
    categories = set()
    for cause in causes:
        categories.add(category_of(cause))

    # Did the agent change a suspicion's root cause between step 1 and step 2?
    relabelled = None                                   # stays None for Unguided
    if taxonomy:
        first = step1_root_causes(repo, skill, model)
        relabelled = 0
        for decision in decisions:
            before = first.get((decision["unit"], decision["label"]))
            if before is not None and before != decision.get("root_cause"):
                relabelled = relabelled + 1

    # How often a static rule agrees with a smell
    rules = rule_root_causes(repo, skill, model)        # {unit: root causes the rules name}
    in_flagged_unit = 0                                 # smells in a unit some rule flags
    same_root_cause = 0                                 # smells whose root cause a rule names too
    for smell in smells:
        if smell["unit"] in rules:
            in_flagged_unit = in_flagged_unit + 1
            if smell.get("root_cause") in rules[smell["unit"]]:
                same_root_cause = same_root_cause + 1

    non_test_units = sizes[repo]["units"] - sizes[repo]["test_units"]
    row = {}
    row["repo"] = repo
    row["skill"] = SKILL_NAMES[skill]
    row["model"] = MODEL_NAMES[model]
    row["decisions"] = len(decisions)
    row["accepted"] = len(smells)
    row["rejected"] = len(decisions) - len(smells)
    row["acceptance_rate_pct"] = percent(len(smells), len(decisions))
    row["smelly_units"] = len(smelly_units)
    row["pct_of_repo_units"] = percent(len(smelly_units), sizes[repo]["units"])
    row["smelly_non_test_units"] = len(smelly_non_test)
    row["pct_of_non_test_units"] = percent(len(smelly_non_test), non_test_units)
    if smelly_units:
        row["smells_per_smelly_unit"] = round(len(smells) / len(smelly_units), 2)
    else:
        row["smells_per_smelly_unit"] = None
    if taxonomy:
        row["root_causes_accepted"] = len(causes)
        row["categories_accepted"] = len(categories)
    else:
        row["root_causes_accepted"] = None
        row["categories_accepted"] = None
    row["relabelled_in_step2"] = relabelled
    row["accepted_in_rule_flagged_unit"] = in_flagged_unit
    row["pct_accepted_in_rule_flagged_unit"] = percent(in_flagged_unit, len(smells))
    if taxonomy:
        row["accepted_same_root_cause_as_a_rule"] = same_root_cause
        row["pct_accepted_same_root_cause_as_a_rule"] = percent(same_root_cause, len(smells))
    else:
        row["accepted_same_root_cause_as_a_rule"] = None
        row["pct_accepted_same_root_cause_as_a_rule"] = None
    return row


def union_rows(sizes):
    """For each repository: units found smelly by at least one of the six runs."""
    rows = []
    for repo in REPOS:
        times_smelly = {}                               # {unit: number of runs that found it smelly}
        per_skill = {}                                  # {skill: units smelly with either model}
        for skill in SKILLS:
            per_skill[skill] = set()
            for model in MODELS:
                units = set()                           # the smelly units of this run
                for smell in smells_of(repo, skill, model):
                    units.add(smell["unit"])
                for unit in units:
                    times_smelly[unit] = times_smelly.get(unit, 0) + 1
                    per_skill[skill].add(unit)

        in_two_or_more = 0
        in_all_six = 0
        for count in times_smelly.values():
            if count >= 2:
                in_two_or_more = in_two_or_more + 1
            if count == 6:
                in_all_six = in_all_six + 1

        row = {}
        row["repo"] = repo
        row["repo_units"] = sizes[repo]["units"]
        row["smelly_in_any_run"] = len(times_smelly)
        row["pct_of_repo_units"] = percent(len(times_smelly), sizes[repo]["units"])
        row["smelly_in_2_or_more_runs"] = in_two_or_more
        row["smelly_in_all_6_runs"] = in_all_six
        for skill in SKILLS:
            row["union_" + SKILL_NAMES[skill]] = len(per_skill[skill])
        rows.append(row)
    return rows


def category_rows():
    """Smells per category (C1 to C12), over all runs of each taxonomy skill."""
    counts = {}                                         # {(skill name, category): number of smells}
    for repo, skill, model in all_runs():
        if skill == "control":                          # Unguided has no categories
            continue
        for smell in smells_of(repo, skill, model):
            if smell.get("root_cause"):
                key = (SKILL_NAMES[skill], category_of(smell["root_cause"]))
                counts[key] = counts.get(key, 0) + 1

    rows = []
    for number in range(1, 13):                         # C1, C2, ..., C12, in that order
        category = "C" + str(number)
        rules = counts.get(("Taxonomy+Rules", category), 0)
        taxonomy = counts.get(("Taxonomy", category), 0)
        if rules + taxonomy == 0:                       # a category no run used
            continue
        rows.append({"category": category, "Taxonomy+Rules": rules,
                     "Taxonomy": taxonomy, "both": rules + taxonomy})
    return rows


def main():
    sizes = repo_sizes()                                # units per repository

    per_run = {}                                        # {(repo, skill, model): numbers of that run}
    for repo, skill, model in all_runs():
        per_run[(repo, skill, model)] = step2_of(repo, skill, model, sizes)
    write_csv(list(per_run.values()), OUT / "step2_per_run.csv")

    summary = {}
    for metric in ["smelly_units", "pct_of_repo_units", "acceptance_rate_pct"]:
        models = compare_models(per_run, metric)
        skills = compare_skills(per_run, metric)
        repos = compare_repos(per_run, metric)
        write_csv(models, OUT / ("step2_models_" + metric + ".csv"))
        write_csv(skills, OUT / ("step2_skills_" + metric + ".csv"))
        write_csv(repos, OUT / ("step2_repos_" + metric + ".csv"))
        summary[metric] = {"model_wins": count_model_wins(models),
                           "skill_order": count_skill_orders(skills),
                           "skill_highest": count_highest(skills)}

    # Agreement with the rules, Taxonomy+Rules against Taxonomy, in each (repo, model)
    # cell. Unguided has no root causes, so it is not in this comparison.
    metric = "pct_accepted_same_root_cause_as_a_rule"
    cells = []
    full_higher = 0
    for repo in REPOS:
        for model in MODELS:
            rules_value = per_run[(repo, "full", model)][metric]
            taxonomy_value = per_run[(repo, "knowledge", model)][metric]
            cells.append({"repo": repo, "model": MODEL_NAMES[model],
                          "Taxonomy+Rules": rules_value, "Taxonomy": taxonomy_value,
                          "full_higher": rules_value > taxonomy_value})
            if rules_value > taxonomy_value:
                full_higher = full_higher + 1
    write_csv(cells, OUT / "step2_rules_agreement_full_vs_knowledge.csv")
    summary["rules_agreement_full_higher_cells"] = full_higher

    # Totals over the 12 taxonomy runs
    decisions = 0
    changed = 0
    smells = 0
    for (repo, skill, model), row in per_run.items():
        if skill == "control":
            continue
        decisions = decisions + row["decisions"]
        changed = changed + row["relabelled_in_step2"]
        smells = smells + row["accepted"]
    summary["relabelled"] = {"decisions_in_taxonomy_runs": decisions, "root_cause_changed": changed}
    summary["smells_in_taxonomy_runs"] = smells

    union = union_rows(sizes)
    write_csv(union, OUT / "step2_union.csv")
    summary["union"] = union
    categories = category_rows()
    write_csv(categories, OUT / "step2_categories.csv")
    summary["categories"] = categories
    write_json(summary, OUT / "step2_summary.json")
    print("wrote", OUT / "step2_*")


if __name__ == "__main__":
    main()
