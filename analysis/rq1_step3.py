"""RQ1, Step 3 (Repair and measure): how much energy the repairs save.

Uses OUR measurement only: review/results.jsonl, written by tools/review.py when
it re-measured every repair after the agent's session. The agent's own
measurements are never read. The repairs in analysis/excluded_repairs.csv count as
measured with the status "excluded" and no saving (common.review_results()).

One line of review/results.jsonl is one repair, with:
  id                the repair's name
  unit              the function or method it repairs
  root_cause        the root cause it removes (empty in Unguided)
  status            our verdict: confirmed, partial, mixed, regressed or negligible,
                    or why it was not measured (over_limit, no_inputs, ...)
  mean_saving_pct   the energy saving averaged over its four inputs, in percent

A repair saves energy when its verdict is confirmed or partial (SAVES in common.py).
Also reads meta.json, for how many units got generated inputs, and
review/submissions.jsonl, for the code of each repair.

Writes to analysis/output/rq1/:
  step3_per_run.csv            one row per run
  step3_models_<metric>.csv    Sonnet vs Haiku in each (repo, skill) cell
  step3_skills_<metric>.csv    the three skills in each (repo, model) cell
  step3_repos_<metric>.csv     the three repositories in each (skill, model) cell
  step3_all_savings.csv        every repair that saves energy, with its saving
  step3_union.csv              functions with a saving repair, per repository, all runs together
  step3_categories.csv         saving repairs per category (taxonomy skills)
  step3_same_function.csv      functions with a saving repair in two or more runs
  step3_identical_repairs.csv  the same edit written in two or more runs, measured each time
  step3_summary.json           the counts behind the comparisons

Run:  python3 analysis/rq1_step3.py
"""

from common import (MEASURED, MODEL_NAMES, OUTPUT_DIR, REPOS, SAVES, SKILL_NAMES,
                    all_runs, category_of, median, percent, quartiles, read_json,
                    read_jsonl, repo_sizes, review_results, run_folder, write_csv, write_json)
from compare import (compare_models, compare_repos, compare_skills,
                     count_highest, count_model_wins, count_skill_orders)

OUT = OUTPUT_DIR / "rq1"   # where this script writes


def review_of(repo, skill, model):
    """Our verdict on every repair of one run (review/results.jsonl), through
    common.review_results()."""
    return review_results(repo, skill, model)


def rounded(value):
    """A number rounded to one decimal, or None when there is no number."""
    if value is None:
        return None
    return round(value, 1)


def step3_of(repo, skill, model, sizes):
    """All Step-3 numbers of one run, as a dictionary."""
    repairs = review_of(repo, skill, model)             # every repair the run submitted

    measured = 0                                        # repairs we measured
    negligible = 0
    mixed = 0
    regressed = 0
    savings = []                                        # the saving of each repair that saves energy
    saved_functions = set()                             # the functions those repairs belong to
    for repair in repairs:
        status = repair["status"]
        if status in MEASURED:
            measured = measured + 1
        if status in SAVES:
            savings.append(repair["mean_saving_pct"])
            saved_functions.add(repair["unit"])
        if status == "negligible":
            negligible = negligible + 1
        if status == "mixed":
            mixed = mixed + 1
        if status == "regressed":
            regressed = regressed + 1

    q1, q3 = quartiles(savings)                         # spread of the savings
    big = 0                                             # savings of at least 50%
    for saving in savings:
        if saving >= 50:
            big = big + 1

    inputs = read_json(run_folder(repo, skill, model) / "meta.json")["inputs"]

    # Units whose inputs could not be generated, and how many of them the input
    # generator refused because the code cannot run in our environment (its
    # reason then starts with "it cannot run here", e.g. a call to a web API)
    failed = inputs.get("failed") or {}                 # {unit: reason}
    cannot_run = 0
    github = 0                                          # reasons that name GitHub
    for reason in failed.values():
        if reason.startswith("it cannot run here"):
            cannot_run = cannot_run + 1
        if "github" in reason.lower():                  # e.g. "performs live GitHub API requests"
            github = github + 1

    row = {}
    row["repo"] = repo
    row["skill"] = SKILL_NAMES[skill]
    row["model"] = MODEL_NAMES[model]
    row["units_inputs_requested"] = inputs["requested"]   # units the agent asked inputs for
    row["units_inputs_ready"] = inputs["ready"]           # units that got usable inputs
    row["pct_inputs_ready"] = percent(inputs["ready"], inputs["requested"])
    row["units_inputs_failed"] = len(failed)
    row["units_inputs_cannot_run_here"] = cannot_run
    row["units_inputs_failed_naming_github"] = github
    row["repairs_submitted"] = len(repairs)
    row["repairs_measured"] = measured
    row["repairs_saving"] = len(savings)
    row["pct_measured_saving"] = percent(len(savings), measured)
    row["repairs_negligible"] = negligible
    row["repairs_mixed"] = mixed
    row["repairs_regressed"] = regressed
    row["functions_with_saving"] = len(saved_functions)
    row["pct_repo_units_with_saving"] = percent(len(saved_functions), sizes[repo]["units"])
    row["median_saving_pct"] = rounded(median(savings))
    row["q1_saving_pct"] = rounded(q1)
    row["q3_saving_pct"] = rounded(q3)
    row["max_saving_pct"] = rounded(max(savings)) if savings else None
    row["savings_at_least_50pct"] = big
    return row


def all_saving_rows():
    """Every repair that saves energy, in every run: one row each."""
    rows = []
    for repo, skill, model in all_runs():
        for repair in review_of(repo, skill, model):
            if repair["status"] not in SAVES:
                continue                                # keep only repairs that save energy
            rows.append({"repo": repo, "skill": SKILL_NAMES[skill], "model": MODEL_NAMES[model],
                         "repair": repair["id"], "unit": repair["unit"],
                         "root_cause": repair.get("root_cause"), "verdict": repair["status"],
                         "saving_pct": round(repair["mean_saving_pct"], 1)})
    return rows


def union_rows(saving_rows, sizes):
    """Per repository: functions with a saving repair in any run, and their best saving."""
    rows = []
    for repo in REPOS:
        best = {}                                       # {function: its best saving over all runs}
        per_skill = {}                                  # {skill name: functions saved by that skill}
        for skill_name in SKILL_NAMES.values():
            per_skill[skill_name] = set()
        for saving in saving_rows:
            if saving["repo"] != repo:
                continue
            unit = saving["unit"]
            if unit not in best or saving["saving_pct"] > best[unit]:
                best[unit] = saving["saving_pct"]
            per_skill[saving["skill"]].add(unit)

        at_least_half = 0
        for value in best.values():
            if value >= 50:
                at_least_half = at_least_half + 1

        row = {}
        row["repo"] = repo
        row["functions_with_saving_any_run"] = len(best)
        row["pct_of_repo_units"] = percent(len(best), sizes[repo]["units"])
        row["median_best_saving_pct"] = rounded(median(list(best.values())))
        row["functions_best_saving_at_least_50pct"] = at_least_half
        for skill_name in SKILL_NAMES.values():
            row["union_" + skill_name] = len(per_skill[skill_name])
        rows.append(row)
    return rows


def category_rows(saving_rows):
    """Saving repairs per category, over the 12 taxonomy runs."""
    savings = {}                                        # {category: [savings]}
    for saving in saving_rows:
        if not saving["root_cause"]:                    # Unguided repairs have no root cause
            continue
        category = category_of(saving["root_cause"])
        if category not in savings:
            savings[category] = []
        savings[category].append(saving["saving_pct"])

    rows = []
    for number in range(1, 13):                         # C1, C2, ..., C12, in that order
        category = "C" + str(number)
        if category not in savings:                     # no saving repair in this category
            continue
        rows.append({"category": category, "saving_repairs": len(savings[category]),
                     "median_saving_pct": rounded(median(savings[category]))})
    return rows


def same_function_rows(saving_rows):
    """Functions that have a saving repair in two or more runs (the repairs may differ)."""
    runs_of = {}                                        # {(repo, function): set of runs}
    for saving in saving_rows:
        key = (saving["repo"], saving["unit"])
        run = saving["skill"] + "/" + saving["model"]
        if key not in runs_of:
            runs_of[key] = set()
        runs_of[key].add(run)

    rows = []
    for (repo, unit), runs in sorted(runs_of.items()):
        if len(runs) >= 2:
            rows.append({"repo": repo, "unit": unit, "runs": len(runs)})
    return rows


def identical_repair_rows():
    """The same edit of the same function, written and measured in two or more runs.

    Each run was measured in its own session, so the difference between their
    savings shows how repeatable our measurement is. Code is compared with all
    whitespace removed.
    """
    groups = {}                                         # {(repo, unit, code): list of measurements}
    for repo, skill, model in all_runs():
        folder = run_folder(repo, skill, model)

        # The code of each repair's unit, by repair id, with whitespace removed
        code_of = {}
        for submission in read_jsonl(folder / "review" / "submissions.jsonl"):
            code = submission["changed"].get(submission["unit"], "")
            code_of[submission["id"]] = "".join(code.split())

        for repair in review_of(repo, skill, model):
            code = code_of.get(repair["id"])
            if repair["status"] not in MEASURED or not code:
                continue                                # only measured repairs whose code we have
            key = (repo, repair["unit"], code)
            if key not in groups:
                groups[key] = []
            groups[key].append({"run": SKILL_NAMES[skill] + "/" + MODEL_NAMES[model],
                                "verdict": repair["status"],
                                "saving": repair["mean_saving_pct"]})

    rows = []
    for (repo, unit, code), measurements in sorted(groups.items()):
        if len(measurements) < 2:                       # measured in one run only
            continue
        savings = []
        verdicts = set()
        for m in measurements:
            savings.append(m["saving"])
            verdicts.add(m["verdict"])
        rows.append({"repo": repo, "unit": unit, "runs": len(measurements),
                     "verdicts": "/".join(sorted(verdicts)),
                     "min_saving_pct": round(min(savings), 1),
                     "max_saving_pct": round(max(savings), 1),
                     "spread_points": round(max(savings) - min(savings), 1)})
    return rows


def same_outcome(verdicts):
    """True when all verdicts agree on whether the repair saves energy.

    `verdicts` is a text like "confirmed/partial": confirmed and partial both
    mean "saves energy", so they agree.
    """
    saves = 0
    does_not = 0
    for verdict in verdicts.split("/"):
        if verdict in SAVES:
            saves = saves + 1
        else:
            does_not = does_not + 1
    return saves == 0 or does_not == 0                  # all one way or all the other


def main():
    sizes = repo_sizes()

    per_run = {}                                        # {(repo, skill, model): numbers of that run}
    for repo, skill, model in all_runs():
        per_run[(repo, skill, model)] = step3_of(repo, skill, model, sizes)
    write_csv(list(per_run.values()), OUT / "step3_per_run.csv")

    summary = {}
    metrics = ["repairs_saving", "functions_with_saving", "pct_measured_saving",
               "median_saving_pct", "repairs_regressed"]
    for metric in metrics:
        models = compare_models(per_run, metric)
        skills = compare_skills(per_run, metric)
        repos = compare_repos(per_run, metric)
        write_csv(models, OUT / ("step3_models_" + metric + ".csv"))
        write_csv(skills, OUT / ("step3_skills_" + metric + ".csv"))
        write_csv(repos, OUT / ("step3_repos_" + metric + ".csv"))
        summary[metric] = {"model_wins": count_model_wins(models),
                           "skill_order": count_skill_orders(skills),
                           "skill_highest": count_highest(skills)}

    # Every repair that saves energy, and totals over the 18 runs
    saving = all_saving_rows()
    write_csv(saving, OUT / "step3_all_savings.csv")
    values = []
    for row in saving:
        values.append(row["saving_pct"])
    q1, q3 = quartiles(values)
    submitted = 0
    measured = 0
    regressed = 0
    inputs_failed = 0
    cannot_run = 0
    for row in per_run.values():
        submitted = submitted + row["repairs_submitted"]
        measured = measured + row["repairs_measured"]
        regressed = regressed + row["repairs_regressed"]
        inputs_failed = inputs_failed + row["units_inputs_failed"]
        cannot_run = cannot_run + row["units_inputs_cannot_run_here"]
    at_least_half = 0
    for value in values:
        if value >= 50:
            at_least_half = at_least_half + 1
    summary["all_runs"] = {
        "repairs_submitted": submitted,
        "repairs_measured": measured,
        "repairs_saving": len(saving),
        "pct_measured_saving": percent(len(saving), measured),
        "repairs_regressed": regressed,
        "median_saving_pct": rounded(median(values)),
        "q1_saving_pct": rounded(q1),
        "q3_saving_pct": rounded(q3),
        "savings_at_least_50pct": at_least_half,
        "units_inputs_failed": inputs_failed,
        "units_inputs_cannot_run_here": cannot_run,
    }

    # Inputs per repository, the six runs added up
    inputs = {}
    for repo in REPOS:
        inputs[repo] = {"units_inputs_requested": 0, "units_inputs_ready": 0,
                        "units_inputs_failed": 0, "units_inputs_cannot_run_here": 0,
                        "units_inputs_failed_naming_github": 0}
    for (repo, skill, model), row in per_run.items():
        for name in inputs[repo]:
            inputs[repo][name] = inputs[repo][name] + row[name]
    summary["inputs_per_repo"] = inputs

    union = union_rows(saving, sizes)
    write_csv(union, OUT / "step3_union.csv")
    summary["union"] = union

    categories = category_rows(saving)
    write_csv(categories, OUT / "step3_categories.csv")
    summary["categories"] = categories

    same = same_function_rows(saving)
    write_csv(same, OUT / "step3_same_function.csv")
    summary["same_function"] = {"functions_saved_in_2_or_more_runs": len(same)}

    identical = identical_repair_rows()
    write_csv(identical, OUT / "step3_identical_repairs.csv")
    spreads = []
    within_5 = 0
    same_verdict = 0
    agree = 0
    for row in identical:
        spreads.append(row["spread_points"])
        if row["spread_points"] <= 5:
            within_5 = within_5 + 1
        if "/" not in row["verdicts"]:                  # one verdict for every run
            same_verdict = same_verdict + 1
        if same_outcome(row["verdicts"]):
            agree = agree + 1
    summary["identical_repairs"] = {
        "repairs": len(identical),
        "same_verdict_in_every_run": same_verdict,
        "same_saves_or_not_in_every_run": agree,
        "median_spread_points": median(spreads),
        "within_5_points": within_5,
    }
    write_json(summary, OUT / "step3_summary.json")
    print("wrote", OUT / "step3_*")


if __name__ == "__main__":
    main()
