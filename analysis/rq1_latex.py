"""Every number the RQ1 text and table use, taken from the output files.

This script computes nothing new. It looks numbers up in the files that
rq1_step1.py, rq1_step2.py and rq1_step3.py wrote, and writes:

  output/rq1/latex/numbers.tex     one LaTeX command per number, e.g.
                                   \\newcommand{\\rqOneSavingRepairs}{186}
  output/rq1/latex/table_runs.tex  the RQ1 table, every cell from a per-run file
  output/rq1/latex/numbers.md      the ledger: for every command and every table
                                   cell, its value, the file and line it comes from,
                                   and what it means

and copies the two .tex files to temp_main_paper/results/generated/, where the
paper text reads them. The paper never types a number by hand: it writes
\\rqOneSavingRepairs, and numbers.md says where 186 comes from.

Run after the three step scripts:  python3 analysis/rq1_latex.py
"""

import csv
import json
import shutil

from common import OUTPUT_DIR, REPO_STATS_FILE, REPOS, ROOT

RQ1 = OUTPUT_DIR / "rq1"                     # where the step scripts wrote
LATEX = RQ1 / "latex"                        # where this script writes
PAPER = ROOT / "temp_main_paper" / "results" / "generated"   # the copy the paper reads

# ---------------------------------------------------------------------------
# Looking numbers up
# ---------------------------------------------------------------------------


def read_rows(file_name):
    """The rows of a .csv (or .tsv) file, each with the line it is on in the file."""
    path = RQ1 / file_name if not file_name.endswith(".tsv") else REPO_STATS_FILE
    delimiter = "\t" if file_name.endswith(".tsv") else ","
    rows = []
    with open(path) as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        line = 1                                     # line 1 is the header
        for row in reader:
            line = line + 1                          # the first row is on line 2
            row["_line"] = line                      # remember where this row is
            rows.append(row)
    return rows


def matches(row, where):
    """True when the row has every value that `where` asks for, e.g. {"repo": "dx-toolkit"}."""
    for column, wanted in where.items():
        if isinstance(wanted, list):                 # one of several allowed values
            if row[column] not in wanted:
                return False
        elif row[column] != wanted:
            return False
    return True


def number(text):
    """A cell of a .csv file as a number (int when it has no decimal part)."""
    value = float(text)
    if value == int(value) and "." not in text:
        return int(value)
    return value


def from_csv(file_name, where, column):
    """The value in `column` of the one row that matches `where`, and its line."""
    found = []
    for row in read_rows(file_name):
        if matches(row, where):
            found.append(row)
    if len(found) != 1:                              # must point at exactly one row
        raise SystemExit(f"{file_name}: {where} matches {len(found)} rows, not 1")
    return number(found[0][column]), f"line {found[0]['_line']}"


def smallest_or_largest(file_name, column, where, largest):
    """The smallest (or largest) value of `column` among rows matching `where`, and its line."""
    best = None
    for row in read_rows(file_name):
        if not matches(row, where) or row[column] == "":
            continue                                 # skip other rows and empty cells
        value = number(row[column])
        if best is None or (value > best[0] if largest else value < best[0]):
            best = (value, row["_line"])
    return best[0], f"line {best[1]}"


def from_json(file_name, keys):
    """The value at keys[0] -> keys[1] -> ... in a .json file, and the line of the last key."""
    path = RQ1 / file_name
    data = json.load(open(path))
    for key in keys:                                 # walk down the keys
        data = data[key]
    # Find the line: each key appears, in order, below the one before it
    lines = open(path).read().splitlines()
    position = 0
    for key in keys:
        while f'"{key}":' not in lines[position]:
            position = position + 1
    return data, f"line {position + 1}"


# ---------------------------------------------------------------------------
# The numbers the RQ1 text uses: (command name, how to find it, what it means)
# ---------------------------------------------------------------------------

SA, DX, CO = "sample-apps", "dx-toolkit", "community"
FULL, KNOW, CTRL = "Taxonomy+Rules", "Taxonomy", "Unguided"


def csv_value(file_name, where, column):
    return lambda: from_csv(file_name, where, column)


def csv_min(file_name, column, where=None):
    return lambda: smallest_or_largest(file_name, column, where or {}, largest=False)


def csv_max(file_name, column, where=None):
    return lambda: smallest_or_largest(file_name, column, where or {}, largest=True)


def json_value(file_name, *keys):
    return lambda: from_json(file_name, list(keys))


NUMBERS = [
    # --- repositories (from experiment/lib/repo_stats.py) ---
    ("rqOneUnitsSa", "repo_stats.tsv", csv_value("repo_stats.tsv", {"repo": "vespa-engine/sample-apps"}, "units"), "units (functions and methods) of sample-apps"),
    ("rqOneUnitsDx", "repo_stats.tsv", csv_value("repo_stats.tsv", {"repo": "dnanexus/dx-toolkit"}, "units"), "units of dx-toolkit"),
    ("rqOneUnitsCo", "repo_stats.tsv", csv_value("repo_stats.tsv", {"repo": "open-telemetry/community"}, "units"), "units of community"),
    ("rqOneTestUnitsDx", "repo_stats.tsv", csv_value("repo_stats.tsv", {"repo": "dnanexus/dx-toolkit"}, "test_units"), "units of dx-toolkit in test files"),

    # --- Step 1 ---
    ("rqOneListedMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "units_listed"), "fewest units listed by a run"),
    ("rqOneListedMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "units_listed"), "most units listed by a run"),
    ("rqOneListedPctMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "pct_of_repo_units"), "smallest share of a repository's units listed by a run (%)"),
    ("rqOneListedPctMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "pct_of_repo_units"), "largest share of a repository's units listed by a run (%)"),
    ("rqOneListedPctDxMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "pct_of_repo_units", {"repo": DX}), "largest share of dx-toolkit's units listed by a run (%)"),
    ("rqOneListedPctOthersMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "pct_of_repo_units", {"repo": [SA, CO]}), "smallest share listed by a run on sample-apps or community (%)"),
    ("rqOneListedSonnetWins", "step1_summary.json", json_value("step1_summary.json", "units_listed", "model_wins", "Sonnet"), "cells (of 9) where Sonnet listed more units than Haiku"),
    ("rqOneListedFullOrder", "step1_summary.json", json_value("step1_summary.json", "units_listed", "skill_order", "full>=knowledge>=control"), "cells (of 6) where Taxonomy+Rules >= Taxonomy >= Unguided in units listed"),
    ("rqOneTestUnitsUngHaikuDx", "step1_per_run.csv", csv_value("step1_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "test_units_listed"), "test units listed by Unguided Haiku on dx-toolkit"),
    ("rqOneRuleCoverFullHighest", "step1_summary.json", json_value("step1_summary.json", "pct_rule_units_listed", "skill_highest", FULL), "cells (of 6) where Taxonomy+Rules listed the largest share of the rule-flagged units"),
    ("rqOneRuleCoverSaSonnetFull", "step1_per_run.csv", csv_value("step1_per_run.csv", {"repo": SA, "skill": FULL, "model": "Sonnet"}, "pct_rule_units_listed"), "share of rule-flagged units listed, sample-apps, Taxonomy+Rules, Sonnet (%)"),
    ("rqOneRuleCoverSaSonnetKnow", "step1_per_run.csv", csv_value("step1_per_run.csv", {"repo": SA, "skill": KNOW, "model": "Sonnet"}, "pct_rule_units_listed"), "the same, Taxonomy (%)"),
    ("rqOneRuleCoverSaSonnetCtrl", "step1_per_run.csv", csv_value("step1_per_run.csv", {"repo": SA, "skill": CTRL, "model": "Sonnet"}, "pct_rule_units_listed"), "the same, Unguided (%)"),
    ("rqOneScanAddedMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "scan_units_added"), "fewest units scan.py added in a Taxonomy+Rules run"),
    ("rqOneScanAddedMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "scan_units_added"), "most units scan.py added in a Taxonomy+Rules run"),
    ("rqOneFlaggedPctMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "pct_listed_flagged_by_rules"), "smallest share of a run's listed units that a rule also flags (%)"),
    ("rqOneFlaggedPctMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "pct_listed_flagged_by_rules"), "largest share of a run's listed units that a rule also flags (%)"),
    ("rqOneAllSixSa", "step1_overlap.csv", csv_value("step1_overlap.csv", {"repo": SA}, "units_listed_by_all_6_runs"), "sample-apps units listed by all six runs"),
    ("rqOneAnySa", "step1_overlap.csv", csv_value("step1_overlap.csv", {"repo": SA}, "units_listed_by_any_run"), "sample-apps units listed by at least one run"),
    ("rqOneAllSixDx", "step1_overlap.csv", csv_value("step1_overlap.csv", {"repo": DX}, "units_listed_by_all_6_runs"), "dx-toolkit units listed by all six runs"),
    ("rqOneAnyDx", "step1_overlap.csv", csv_value("step1_overlap.csv", {"repo": DX}, "units_listed_by_any_run"), "dx-toolkit units listed by at least one run"),
    ("rqOneAllSixCo", "step1_overlap.csv", csv_value("step1_overlap.csv", {"repo": CO}, "units_listed_by_all_6_runs"), "community units listed by all six runs"),
    ("rqOneAnyCo", "step1_overlap.csv", csv_value("step1_overlap.csv", {"repo": CO}, "units_listed_by_any_run"), "community units listed by at least one run"),

    # --- Step 2 ---
    ("rqOneSmellyPctMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "pct_of_repo_units"), "smallest share of a repository's units one run found smelly (%)"),
    ("rqOneSmellyPctMax", "step2_per_run.csv", csv_max("step2_per_run.csv", "pct_of_repo_units"), "largest share of a repository's units one run found smelly (%)"),
    ("rqOneUnionSa", "step2_union.csv", csv_value("step2_union.csv", {"repo": SA}, "smelly_in_any_run"), "sample-apps units smelly in at least one run"),
    ("rqOneUnionPctSa", "step2_union.csv", csv_value("step2_union.csv", {"repo": SA}, "pct_of_repo_units"), "the same, as % of its units"),
    ("rqOneUnionDx", "step2_union.csv", csv_value("step2_union.csv", {"repo": DX}, "smelly_in_any_run"), "dx-toolkit units smelly in at least one run"),
    ("rqOneUnionPctDx", "step2_union.csv", csv_value("step2_union.csv", {"repo": DX}, "pct_of_repo_units"), "the same, as % of its units"),
    ("rqOneUnionCo", "step2_union.csv", csv_value("step2_union.csv", {"repo": CO}, "smelly_in_any_run"), "community units smelly in at least one run"),
    ("rqOneUnionPctCo", "step2_union.csv", csv_value("step2_union.csv", {"repo": CO}, "pct_of_repo_units"), "the same, as % of its units"),
    ("rqOneSmellyFullOverCtrl", "step2_summary.json", json_value("step2_summary.json", "smelly_units", "skill_order", "full>=control"), "cells (of 6) where Taxonomy+Rules found at least as many smelly units as Unguided"),
    ("rqOneSmellyFullOrder", "step2_summary.json", json_value("step2_summary.json", "smelly_units", "skill_order", "full>=knowledge>=control"), "cells (of 6) where Taxonomy+Rules >= Taxonomy >= Unguided in smelly units"),
    ("rqOneSmellySaHaikuKnow", "step2_per_run.csv", csv_value("step2_per_run.csv", {"repo": SA, "skill": KNOW, "model": "Haiku"}, "smelly_units"), "smelly units, sample-apps, Taxonomy, Haiku"),
    ("rqOneSmellySaHaikuFull", "step2_per_run.csv", csv_value("step2_per_run.csv", {"repo": SA, "skill": FULL, "model": "Haiku"}, "smelly_units"), "smelly units, sample-apps, Taxonomy+Rules, Haiku"),
    ("rqOneSmellyCoHaikuKnow", "step2_per_run.csv", csv_value("step2_per_run.csv", {"repo": CO, "skill": KNOW, "model": "Haiku"}, "smelly_units"), "smelly units, community, Taxonomy, Haiku"),
    ("rqOneSmellyCoHaikuFull", "step2_per_run.csv", csv_value("step2_per_run.csv", {"repo": CO, "skill": FULL, "model": "Haiku"}, "smelly_units"), "smelly units, community, Taxonomy+Rules, Haiku"),
    ("rqOneSmellySonnetWins", "step2_summary.json", json_value("step2_summary.json", "smelly_units", "model_wins", "Sonnet"), "cells (of 9) where Sonnet found more smelly units than Haiku"),
    ("rqOneAcceptUngHaikuMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "acceptance_rate_pct", {"skill": CTRL, "model": "Haiku"}), "lowest share of suspicions Unguided Haiku accepted (%)"),
    ("rqOneAcceptUngHaikuMax", "step2_per_run.csv", csv_max("step2_per_run.csv", "acceptance_rate_pct", {"skill": CTRL, "model": "Haiku"}), "highest share of suspicions Unguided Haiku accepted (%)"),
    ("rqOneAcceptOthersMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "acceptance_rate_pct", {"skill": [FULL, KNOW]}), "lowest acceptance rate of any taxonomy run (%)"),
    ("rqOneSmellyPctDxMax", "step2_per_run.csv", csv_max("step2_per_run.csv", "pct_of_repo_units", {"repo": DX}), "largest share of dx-toolkit's units one run found smelly (%)"),
    ("rqOneSmellyPctOthersMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "pct_of_repo_units", {"repo": [SA, CO]}), "smallest share on sample-apps or community (%)"),
    ("rqOneSmellyNonTestDxMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "pct_of_non_test_units", {"repo": DX}), "smallest share of dx-toolkit's non-test units one run found smelly (%)"),
    ("rqOneSmellyNonTestDxMax", "step2_per_run.csv", csv_max("step2_per_run.csv", "pct_of_non_test_units", {"repo": DX}), "largest share of dx-toolkit's non-test units one run found smelly (%)"),
    ("rqOneRulesAgreeCells", "step2_summary.json", json_value("step2_summary.json", "rules_agreement_full_higher_cells"), "cells (of 6) where more smells share a rule's root cause with Taxonomy+Rules than with Taxonomy"),
    ("rqOneRelabelled", "step2_summary.json", json_value("step2_summary.json", "relabelled", "root_cause_changed"), "decisions whose root cause differs from step 1"),
    ("rqOneTaxDecisions", "step2_summary.json", json_value("step2_summary.json", "relabelled", "decisions_in_taxonomy_runs"), "decisions in the 12 taxonomy runs"),
    ("rqOneTaxSmells", "step2_summary.json", json_value("step2_summary.json", "smells_in_taxonomy_runs"), "smells in the 12 taxonomy runs"),
    ("rqOneCatCOne", "step2_categories.csv", csv_value("step2_categories.csv", {"category": "C1"}, "both"), "smells in category C1, both taxonomy skills"),
    ("rqOneCatCEight", "step2_categories.csv", csv_value("step2_categories.csv", {"category": "C8"}, "both"), "smells in category C8"),
    ("rqOneCatCThree", "step2_categories.csv", csv_value("step2_categories.csv", {"category": "C3"}, "both"), "smells in category C3"),
    ("rqOneCatCSix", "step2_categories.csv", csv_value("step2_categories.csv", {"category": "C6"}, "both"), "smells in category C6"),
    ("rqOneCatCTen", "step2_categories.csv", csv_value("step2_categories.csv", {"category": "C10"}, "both"), "smells in category C10"),

    # --- Step 3 ---
    ("rqOneSubmitted", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_submitted"), "repairs submitted, all 18 runs"),
    ("rqOneMeasured", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_measured"), "repairs we measured"),
    ("rqOneSavingRepairs", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_saving"), "repairs that save energy (confirmed or partial)"),
    ("rqOneSavingPct", "step3_summary.json", json_value("step3_summary.json", "all_runs", "pct_measured_saving"), "share of measured repairs that save energy (%)"),
    ("rqOneMedianSaving", "step3_summary.json", json_value("step3_summary.json", "all_runs", "median_saving_pct"), "median saving of the repairs that save energy (%)"),
    ("rqOneQOneSaving", "step3_summary.json", json_value("step3_summary.json", "all_runs", "q1_saving_pct"), "25th percentile of those savings (%)"),
    ("rqOneQThreeSaving", "step3_summary.json", json_value("step3_summary.json", "all_runs", "q3_saving_pct"), "75th percentile of those savings (%)"),
    ("rqOneHalfSaving", "step3_summary.json", json_value("step3_summary.json", "all_runs", "savings_at_least_50pct"), "repairs saving at least 50%"),
    ("rqOneRegressed", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_regressed"), "repairs that cost more energy (regressed)"),
    ("rqOneSavedFnSa", "step3_union.csv", csv_value("step3_union.csv", {"repo": SA}, "functions_with_saving_any_run"), "sample-apps functions with a saving repair in some run"),
    ("rqOneSavedFnDx", "step3_union.csv", csv_value("step3_union.csv", {"repo": DX}, "functions_with_saving_any_run"), "dx-toolkit functions with a saving repair in some run"),
    ("rqOneSavedFnCo", "step3_union.csv", csv_value("step3_union.csv", {"repo": CO}, "functions_with_saving_any_run"), "community functions with a saving repair in some run"),
    ("rqOneSavingFullOverCtrl", "step3_summary.json", json_value("step3_summary.json", "repairs_saving", "skill_order", "full>=control"), "cells (of 6) where Taxonomy+Rules has at least as many saving repairs as Unguided"),
    ("rqOneSavingFullOrder", "step3_summary.json", json_value("step3_summary.json", "repairs_saving", "skill_order", "full>=knowledge>=control"), "cells (of 6) where the full order holds for saving repairs"),
    ("rqOneSavingKnowHighest", "step3_summary.json", json_value("step3_summary.json", "repairs_saving", "skill_highest", KNOW), "cells (of 6) where Taxonomy has the most saving repairs (ties included)"),
    ("rqOneSonnetMeasuredMin", "step3_per_run.csv", csv_min("step3_per_run.csv", "repairs_measured", {"model": "Sonnet", "repo": [SA, DX]}), "fewest repairs measured in a Sonnet run on sample-apps or dx-toolkit"),
    ("rqOneSonnetSavingMin", "step3_per_run.csv", csv_min("step3_per_run.csv", "repairs_saving", {"model": "Sonnet", "repo": [SA, DX]}), "fewest saving repairs in those runs"),
    ("rqOneSonnetSavingMax", "step3_per_run.csv", csv_max("step3_per_run.csv", "repairs_saving", {"model": "Sonnet", "repo": [SA, DX]}), "most saving repairs in those runs"),
    ("rqOneMedianSaSonnetCtrl", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": SA, "skill": CTRL, "model": "Sonnet"}, "median_saving_pct"), "median saving, sample-apps, Unguided, Sonnet (%)"),
    ("rqOneMedianSaSonnetFull", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": SA, "skill": FULL, "model": "Sonnet"}, "median_saving_pct"), "median saving, sample-apps, Taxonomy+Rules, Sonnet (%)"),
    ("rqOneMedianSaSonnetKnow", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": SA, "skill": KNOW, "model": "Sonnet"}, "median_saving_pct"), "median saving, sample-apps, Taxonomy, Sonnet (%)"),
    ("rqOneRegressedMax", "step3_per_run.csv", csv_max("step3_per_run.csv", "repairs_regressed"), "most regressed repairs in one run"),
    ("rqOneRegressedDxUngSonnet", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Sonnet"}, "repairs_regressed"), "regressed repairs, dx-toolkit, Unguided, Sonnet"),
    ("rqOneSavedFnSonnetWins", "step3_summary.json", json_value("step3_summary.json", "functions_with_saving", "model_wins", "Sonnet"), "cells (of 9) where Sonnet has more functions with a saving repair"),
    ("rqOneSavedFnTies", "step3_summary.json", json_value("step3_summary.json", "functions_with_saving", "model_wins", "tie"), "cells (of 9) where both models have the same number"),
    ("rqOneInputsReadyDxUngHaiku", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "units_inputs_ready"), "units with usable inputs, dx-toolkit, Unguided, Haiku"),
    ("rqOneInputsAskedDxUngHaiku", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "units_inputs_requested"), "units it asked inputs for"),
    ("rqOneInputsReadyCoHaikuMin", "step3_per_run.csv", csv_min("step3_per_run.csv", "units_inputs_ready", {"repo": CO, "model": "Haiku"}), "fewest units with usable inputs, community, Haiku"),
    ("rqOneInputsReadyCoHaikuMax", "step3_per_run.csv", csv_max("step3_per_run.csv", "units_inputs_ready", {"repo": CO, "model": "Haiku"}), "most units with usable inputs, community, Haiku"),
    ("rqOneInputsAskedCoHaikuMin", "step3_per_run.csv", csv_min("step3_per_run.csv", "units_inputs_requested", {"repo": CO, "model": "Haiku"}), "fewest units asked for, community, Haiku"),
    ("rqOneInputsAskedCoHaikuMax", "step3_per_run.csv", csv_max("step3_per_run.csv", "units_inputs_requested", {"repo": CO, "model": "Haiku"}), "most units asked for, community, Haiku"),
    ("rqOneInputsFailed", "step3_summary.json", json_value("step3_summary.json", "all_runs", "units_inputs_failed"), "units for which no usable inputs could be generated, all runs"),
    ("rqOneInputsCannotRun", "step3_summary.json", json_value("step3_summary.json", "all_runs", "units_inputs_cannot_run_here"), "of those, refused because the code cannot run in our environment"),
    ("rqOneInputsFailedDxUngHaiku", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "units_inputs_failed"), "units without inputs, dx-toolkit, Unguided, Haiku"),
    ("rqOneInputsCannotRunDxUngHaiku", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "units_inputs_cannot_run_here"), "of those, refused because the code cannot run here"),
    ("rqOneMedianDxMin", "step3_per_run.csv", csv_min("step3_per_run.csv", "median_saving_pct", {"repo": DX}), "lowest median saving of a dx-toolkit run (%)"),
    ("rqOneMedianDxMax", "step3_per_run.csv", csv_max("step3_per_run.csv", "median_saving_pct", {"repo": DX}), "highest median saving of a dx-toolkit run (%)"),
    ("rqOneMedianCoMin", "step3_per_run.csv", csv_min("step3_per_run.csv", "median_saving_pct", {"repo": CO}), "lowest median saving of a community run (%)"),
    ("rqOneMedianCoMax", "step3_per_run.csv", csv_max("step3_per_run.csv", "median_saving_pct", {"repo": CO}), "highest median saving of a community run (%)"),
    ("rqOneIdentical", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "repairs"), "repairs written identically in two or more runs"),
    ("rqOneIdenticalSpread", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "median_spread_points"), "median difference of their savings, in percentage points"),
    ("rqOneIdenticalWithinFive", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "within_5_points"), "of those, within 5 points"),
    ("rqOneIdenticalSameOutcome", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "same_saves_or_not_in_every_run"), "of those, same outcome (saves or not) in every run"),
    ("rqOneSameFunction", "step3_summary.json", json_value("step3_summary.json", "same_function", "functions_saved_in_2_or_more_runs"), "functions with a saving repair in two or more runs"),
    ("rqOneSaveCatCSevenN", "step3_categories.csv", csv_value("step3_categories.csv", {"category": "C7"}, "saving_repairs"), "saving repairs in category C7"),
    ("rqOneSaveCatCSevenMed", "step3_categories.csv", csv_value("step3_categories.csv", {"category": "C7"}, "median_saving_pct"), "their median saving (%)"),
    ("rqOneSaveCatCSixN", "step3_categories.csv", csv_value("step3_categories.csv", {"category": "C6"}, "saving_repairs"), "saving repairs in category C6"),
    ("rqOneSaveCatCSixMed", "step3_categories.csv", csv_value("step3_categories.csv", {"category": "C6"}, "median_saving_pct"), "their median saving (%)"),
    ("rqOneSaveCatCTenN", "step3_categories.csv", csv_value("step3_categories.csv", {"category": "C10"}, "saving_repairs"), "saving repairs in category C10"),
    ("rqOneSaveCatCOneN", "step3_categories.csv", csv_value("step3_categories.csv", {"category": "C1"}, "saving_repairs"), "saving repairs in category C1"),
]


def formatted(value):
    """How a number is printed in the paper.

    Whole counts get a thousands comma (2543 -> 2,543). Everything else (the
    percentages) keeps exactly one decimal, also when it is .0 (23.0 stays 23.0).
    """
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.1f}"


# ---------------------------------------------------------------------------
# The RQ1 table: one row per (repo, skill), one block of columns per model
# ---------------------------------------------------------------------------

def table_cells():
    """Every cell of the RQ1 table, with its source, as a list of dicts."""
    cells = []
    for repo in REPOS:
        for skill in (FULL, KNOW, CTRL):
            for model in ("Sonnet", "Haiku"):
                where = {"repo": repo, "skill": skill, "model": model}
                for column, file_name, field in (
                        ("Listed", "step1_per_run.csv", "units_listed"),
                        ("Smelly", "step2_per_run.csv", "smelly_units"),
                        ("Smelly %", "step2_per_run.csv", "pct_of_repo_units"),
                        ("Measured", "step3_per_run.csv", "repairs_measured"),
                        ("Saving", "step3_per_run.csv", "repairs_saving"),
                        ("Median %", "step3_per_run.csv", "median_saving_pct")):
                    value, line = from_csv(file_name, where, field)
                    cells.append({"repo": repo, "skill": skill, "model": model, "column": column,
                                  "value": value, "file": file_name, "line": line, "field": field})
    return cells


def table_tex(cells):
    """The LaTeX of the RQ1 table, built from the cells."""
    def cell(repo, skill, model, column):
        for c in cells:
            if c["repo"] == repo and c["skill"] == skill and c["model"] == model and c["column"] == column:
                return formatted(c["value"])
        raise SystemExit(f"missing table cell {repo} {skill} {model} {column}")

    macro = {FULL: r"\taxorules", KNOW: r"\taxo", CTRL: r"\unguided"}
    lines = [
        "% Generated by analysis/rq1_latex.py from step1/2/3_per_run.csv. Do not edit by hand;",
        "% the source of every cell is in analysis/output/rq1/latex/numbers.md.",
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{RQ1: one run per repository, skill and model. \textit{Listed}: units listed in Step~1."
        r" \textit{Smelly}: units with an accepted smell in Step~2, and their share of the repository's units."
        r" \textit{Saving / Measured}: repairs that save energy (confirmed or partial) out of the repairs we measured in Step~3."
        r" \textit{Median}: median energy saving of those repairs.}",
        r"\label{tab:rq1-runs}",
        r"\footnotesize",
        r"\begin{tabular}{@{}llrrrrrrrr@{}}",
        r"\toprule",
        r" & & \multicolumn{4}{c}{\textbf{Sonnet}} & \multicolumn{4}{c}{\textbf{Haiku}} \\",
        r"\cmidrule(lr){3-6}\cmidrule(l){7-10}",
        r"\textbf{Repository} & \textbf{Skill} & Listed & Smelly (\%) & Saving / Measured & Median (\%)"
        r" & Listed & Smelly (\%) & Saving / Measured & Median (\%) \\",
        r"\midrule",
    ]
    for repo in REPOS:
        for i, skill in enumerate((FULL, KNOW, CTRL)):
            name = r"\texttt{" + repo + "}" if i == 0 else ""
            parts = [name, macro[skill]]
            for model in ("Sonnet", "Haiku"):
                parts.append(cell(repo, skill, model, "Listed"))
                parts.append(cell(repo, skill, model, "Smelly") + " (" + cell(repo, skill, model, "Smelly %") + ")")
                parts.append(cell(repo, skill, model, "Saving") + " / " + cell(repo, skill, model, "Measured"))
                parts.append(cell(repo, skill, model, "Median %"))
            lines.append(" & ".join(parts) + r" \\")
        if repo != REPOS[-1]:
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines) + "\n"


def main():
    LATEX.mkdir(parents=True, exist_ok=True)
    PAPER.mkdir(parents=True, exist_ok=True)

    tex = ["% Generated by analysis/rq1_latex.py. Do not edit by hand.",
           "% Where each number comes from: analysis/output/rq1/latex/numbers.md"]
    ledger = ["# RQ1 numbers: where each one comes from",
              "",
              "Generated by `analysis/rq1_latex.py`. Every number in the RQ1 text is a LaTeX",
              "command from `numbers.tex`; this table gives its value, the file it is read from",
              "(in `analysis/output/rq1/`, or `analysis/output/repo_stats.tsv`), the line in",
              "that file, and what it means. The table cells follow at the end.",
              "",
              "| Command | Value | File | Line | What it is |",
              "|---|---|---|---|---|"]
    for name, file_name, find, meaning in NUMBERS:
        value, line = find()                         # look the number up
        tex.append(f"\\newcommand{{\\{name}}}{{{formatted(value)}}}")
        ledger.append(f"| `\\{name}` | {formatted(value)} | `{file_name}` | {line} | {meaning} |")

    cells = table_cells()
    ledger += ["", "## Table~\\ref{tab:rq1-runs} (`table_runs.tex`)", "",
               "| Repository | Skill | Model | Column | Value | File | Line | Field |",
               "|---|---|---|---|---|---|---|---|"]
    for c in cells:
        ledger.append(f"| {c['repo']} | {c['skill']} | {c['model']} | {c['column']} | "
                      f"{formatted(c['value'])} | `{c['file']}` | {c['line']} | `{c['field']}` |")

    (LATEX / "numbers.tex").write_text("\n".join(tex) + "\n")
    (LATEX / "numbers.md").write_text("\n".join(ledger) + "\n")
    (LATEX / "table_runs.tex").write_text(table_tex(cells))
    for name in ("numbers.tex", "table_runs.tex", "numbers.md"):   # the copy the paper reads
        shutil.copy(LATEX / name, PAPER / name)
    print(f"wrote {len(NUMBERS)} numbers and {len(cells)} table cells to {LATEX} and {PAPER}")


if __name__ == "__main__":
    main()
