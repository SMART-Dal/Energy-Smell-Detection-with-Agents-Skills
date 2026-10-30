"""Every number the RQ1 text and tables use, taken from the output files.

This script computes nothing new. It looks numbers up in the files that the
other rq1_*.py scripts wrote, and writes, to output/rq1/latex/:

  numbers.tex            one LaTeX command per number, e.g.
                         \\newcommand{\\rqOneSavingRepairs}{186}
  numbers.json           the same numbers, each with its file, line, meaning and
                         the script that wrote the file (read by rq1_render.py)
  table_runs.tex         Table: one row per repository and skill, a column block per model
  table_together.tex     Table: the six runs on a repository together
  table_categories.tex   Table: from smells to confirmed repairs, per category
  table_repairs.tex      Table: verdicts by skill, model, size, change and rule flag
  table_cost.tex         Table: cost, tokens, time, tool calls and subagents
  numbers.md             the ledger: for every command and every table cell, its
                         value, the file and line it comes from, and what it means

and copies them to temp_main_paper/results/generated/, where the paper reads
them. The paper never types a number by hand.

Run after the other rq1_*.py scripts:  python3 analysis/rq1_latex.py
"""

import csv
import json
import shutil

from common import OUTPUT_DIR, REPO_STATS_FILE, REPOS, ROOT

RQ1 = OUTPUT_DIR / "rq1"                     # where the other scripts wrote
LATEX = RQ1 / "latex"                        # where this script writes
PAPER = ROOT / "temp_main_paper" / "results" / "generated"   # the copy the paper reads

# Which script and function wrote each output file (for numbers.md and numbers.json)
MADE_BY = {
    "repo_stats.tsv": "experiment/lib/repo_stats.py, count_units()",
    "step1_per_run.csv": "analysis/rq1_step1.py, step1_of()",
    "step1_summary.json": "analysis/rq1_step1.py, main()",
    "step2_per_run.csv": "analysis/rq1_step2.py, step2_of()",
    "step2_summary.json": "analysis/rq1_step2.py, main()",
    "step3_per_run.csv": "analysis/rq1_step3.py, step3_of()",
    "step3_summary.json": "analysis/rq1_step3.py, main()",
    "together_per_repo.csv": "analysis/rq1_together.py, together_row()",
    "categories_funnel.csv": "analysis/rq1_categories.py, funnel_row()",
    "root_causes_funnel.csv": "analysis/rq1_categories.py, funnel_row()",
    "categories_summary.json": "analysis/rq1_categories.py, main()",
    "repairs_by_skill.csv": "analysis/rq1_repairs.py, profile_table() and outcome()",
    "repairs_by_model.csv": "analysis/rq1_repairs.py, profile_table() and outcome()",
    "repairs_by_size.csv": "analysis/rq1_repairs.py, grouped_table() and outcome()",
    "repairs_by_change.csv": "analysis/rq1_repairs.py, grouped_table() and outcome()",
    "repairs_by_rule_flag.csv": "analysis/rq1_repairs.py, rule_flag_table() and outcome()",
    "repairs_summary.json": "analysis/rq1_repairs.py, main(); intervals by interval() and bootstrap.py",
    "cost_per_run.csv": "analysis/rq1_cost.py, cost_of()",
    "cost_per_skill_model.csv": "analysis/rq1_cost.py, added_up()",
    "cost_per_model.csv": "analysis/rq1_cost.py, added_up()",
    "cost_summary.json": "analysis/rq1_cost.py, added_up()",
}

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


def csv_value(file_name, where, column):
    return lambda: from_csv(file_name, where, column)


def csv_min(file_name, column, where=None):
    return lambda: smallest_or_largest(file_name, column, where or {}, largest=False)


def csv_max(file_name, column, where=None):
    return lambda: smallest_or_largest(file_name, column, where or {}, largest=True)


def json_value(file_name, *keys):
    return lambda: from_json(file_name, list(keys))


# ---------------------------------------------------------------------------
# The numbers the RQ1 text uses: (command name, file, how to find it, what it means)
# ---------------------------------------------------------------------------

SA, DX, CO = "sample-apps", "dx-toolkit", "community"
FULL, KNOW, CTRL = "Taxonomy+Rules", "Taxonomy", "Unguided"

NUMBERS = [
    # --- the method of the intervals ---
    ("rqOneComparisonLevel", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_unflagged_minus_flagged", "level_pct"), "width of the Bonferroni-adjusted intervals of the three comparisons (%)"),

    # --- Step 1 and Step 2 ---
    ("rqOneScanAddedMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "scan_units_added"), "fewest units the comparison with the rules added in a Taxonomy+Rules run"),
    ("rqOneScanAddedMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "scan_units_added"), "most units the comparison with the rules added in a Taxonomy+Rules run"),
    ("rqOneAcceptUngHaikuMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "acceptance_rate_pct", {"skill": CTRL, "model": "Haiku"}), "lowest share of suspicions Unguided Haiku accepted (%)"),
    ("rqOneAcceptUngHaikuMax", "step2_per_run.csv", csv_max("step2_per_run.csv", "acceptance_rate_pct", {"skill": CTRL, "model": "Haiku"}), "highest share of suspicions Unguided Haiku accepted (%)"),
    ("rqOneAcceptTaxMin", "step2_per_run.csv", csv_min("step2_per_run.csv", "acceptance_rate_pct", {"skill": [FULL, KNOW]}), "lowest acceptance rate of any run of the two taxonomy skills (%)"),
    ("rqOneRelabelled", "step2_summary.json", json_value("step2_summary.json", "relabelled", "root_cause_changed"), "step-2 decisions whose root cause differs from step 1"),
    ("rqOneTaxDecisions", "step2_summary.json", json_value("step2_summary.json", "relabelled", "decisions_in_taxonomy_runs"), "step-2 decisions in the 12 taxonomy runs"),
    ("rqOneUnitsDx", "repo_stats.tsv", csv_value("repo_stats.tsv", {"repo": "dnanexus/dx-toolkit"}, "units"), "units (functions and methods) of dx-toolkit"),
    ("rqOneTestUnitsDx", "repo_stats.tsv", csv_value("repo_stats.tsv", {"repo": "dnanexus/dx-toolkit"}, "test_units"), "units of dx-toolkit in test files"),
    ("rqOneTestListedDxHaikuMin", "step1_per_run.csv", csv_min("step1_per_run.csv", "test_units_listed", {"repo": DX, "model": "Haiku"}), "fewest test units a Haiku run listed on dx-toolkit"),
    ("rqOneTestListedDxHaikuMax", "step1_per_run.csv", csv_max("step1_per_run.csv", "test_units_listed", {"repo": DX, "model": "Haiku"}), "most test units a Haiku run listed on dx-toolkit"),
    ("rqOneRulesAgreeCells", "step2_summary.json", json_value("step2_summary.json", "rules_agreement_full_higher_cells"), "(repo, model) pairs, of 6, where more smells share a rule's root cause with Taxonomy+Rules than with Taxonomy"),

    # --- categories ---
    ("rqOneTaxSmells", "categories_summary.json", json_value("categories_summary.json", "smells"), "smells in the 12 taxonomy runs"),
    ("rqOneCEightSFourSmells", "root_causes_funnel.csv", csv_value("root_causes_funnel.csv", {"id": "C8.S4"}, "smells"), "smells of root cause C8.S4 (Redundant Data Fetching)"),
    ("rqOneCEightSFourDx", "root_causes_funnel.csv", csv_value("root_causes_funnel.csv", {"id": "C8.S4"}, "smells_dx-toolkit"), "of those, smells in dx-toolkit"),
    ("rqOneCEightSFourSubmitted", "root_causes_funnel.csv", csv_value("root_causes_funnel.csv", {"id": "C8.S4"}, "submitted"), "repairs submitted for C8.S4"),

    # --- Step 3 ---
    ("rqOneSubmitted", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_submitted"), "repairs submitted, all 18 runs"),
    ("rqOneMeasured", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_measured"), "repairs we measured"),
    ("rqOneSavingRepairs", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_saving"), "repairs confirmed (confirmed or partial)"),
    ("rqOneSavingPct", "step3_summary.json", json_value("step3_summary.json", "all_runs", "pct_measured_saving"), "share of measured repairs that are confirmed (%)"),
    ("rqOneSavingPctLow", "repairs_summary.json", json_value("repairs_summary.json", "pct_confirmed_all", "low"), "lower end of its 95% interval (%)"),
    ("rqOneSavingPctHigh", "repairs_summary.json", json_value("repairs_summary.json", "pct_confirmed_all", "high"), "upper end of its 95% interval (%)"),
    ("rqOneMedianSaving", "step3_summary.json", json_value("step3_summary.json", "all_runs", "median_saving_pct"), "median saving of the confirmed repairs (%)"),
    ("rqOneMedianSavingLow", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_all", "low"), "lower end of its 95% interval (%)"),
    ("rqOneMedianSavingHigh", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_all", "high"), "upper end of its 95% interval (%)"),
    ("rqOneRegressed", "step3_summary.json", json_value("step3_summary.json", "all_runs", "repairs_regressed"), "repairs that regressed"),
    ("rqOneSavedFnSonnetWins", "step3_summary.json", json_value("step3_summary.json", "functions_with_saving", "model_wins", "Sonnet"), "(repo, skill) pairs, of 9, where Sonnet has more functions with a confirmed repair"),
    ("rqOneInputsReadyDxUngHaiku", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "units_inputs_ready"), "units with usable inputs, dx-toolkit, Unguided, Haiku"),
    ("rqOneInputsAskedDxUngHaiku", "step3_per_run.csv", csv_value("step3_per_run.csv", {"repo": DX, "skill": CTRL, "model": "Haiku"}, "units_inputs_requested"), "units it asked inputs for"),
    ("rqOneInputsFailedCo", "step3_summary.json", json_value("step3_summary.json", "inputs_per_repo", "community", "units_inputs_failed"), "community units whose inputs failed, six runs added up"),
    ("rqOneInputsAskedCo", "step3_summary.json", json_value("step3_summary.json", "inputs_per_repo", "community", "units_inputs_requested"), "community units the six runs asked inputs for"),
    ("rqOneInputsGithubCo", "step3_summary.json", json_value("step3_summary.json", "inputs_per_repo", "community", "units_inputs_failed_naming_github"), "of the failed ones, those whose reason names GitHub"),
    ("rqOneIdentical", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "repairs"), "repairs written identically in two or more runs"),
    ("rqOneIdenticalSpread", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "median_spread_points"), "median difference of their savings (percentage points)"),
    ("rqOneIdenticalSameOutcome", "step3_summary.json", json_value("step3_summary.json", "identical_repairs", "same_saves_or_not_in_every_run"), "of those, same outcome (confirmed or not) in every run"),

    # --- the repairs themselves ---
    ("rqOneFlaggedRepairs", "repairs_by_rule_flag.csv", csv_value("repairs_by_rule_flag.csv", {"within": "all", "rule_flagged_unit": "True"}, "measured"), "measured repairs in units a static rule flags"),
    ("rqOneFlagDiff", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_unflagged_minus_flagged", "value"), "median saving of unflagged minus flagged units (points)"),
    ("rqOneFlagDiffLow", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_unflagged_minus_flagged", "low"), "lower end of its interval"),
    ("rqOneFlagDiffHigh", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_unflagged_minus_flagged", "high"), "upper end of its interval"),
    ("rqOneMedianLines", "repairs_summary.json", json_value("repairs_summary.json", "median_lines_changed"), "median lines changed by a measured repair"),
    ("rqOneMultiFunction", "repairs_summary.json", json_value("repairs_summary.json", "repairs_changing_more_than_one_function"), "measured repairs that change more than one function"),
    ("rqOneSmallDiff", "repairs_summary.json", json_value("repairs_summary.json", "pct_confirmed_larger_minus_small", "value"), "confirmed share of larger repairs minus 1-2-line repairs (points)"),
    ("rqOneSmallDiffLow", "repairs_summary.json", json_value("repairs_summary.json", "pct_confirmed_larger_minus_small", "low"), "lower end of its interval"),
    ("rqOneSmallDiffHigh", "repairs_summary.json", json_value("repairs_summary.json", "pct_confirmed_larger_minus_small", "high"), "upper end of its interval"),
    ("rqOneLoopsMedian", "repairs_by_change.csv", csv_value("repairs_by_change.csv", {"change_group": "Changes the loops"}, "median_saving_pct"), "median saving of confirmed repairs that change the loops (%)"),
    ("rqOneLoopsDiff", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_loops_changed_minus_others", "value"), "their median saving minus that of the other repairs (points)"),
    ("rqOneLoopsDiffLow", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_loops_changed_minus_others", "low"), "lower end of its interval"),
    ("rqOneLoopsDiffHigh", "repairs_summary.json", json_value("repairs_summary.json", "median_saving_loops_changed_minus_others", "high"), "upper end of its interval"),

    # --- cost ---
    ("rqOneCostTotal", "cost_summary.json", json_value("cost_summary.json", "cost_usd"), "cost of the 18 runs, as Claude Code reported it (USD)"),
    ("rqOneCostPerConfirmed", "cost_summary.json", json_value("cost_summary.json", "usd_per_confirmed_repair"), "that cost per confirmed repair (USD)"),
    ("rqOneSubagentsMax", "cost_per_run.csv", csv_max("cost_per_run.csv", "subagents"), "most subagents started in one run"),
    ("rqOneCostOutlier", "cost_per_run.csv", csv_value("cost_per_run.csv", {"repo": DX, "skill": KNOW, "model": "Haiku"}, "cost_usd"), "cost of the Taxonomy Haiku run on dx-toolkit (USD)"),
    ("rqOneMinutesOutlier", "cost_per_run.csv", csv_value("cost_per_run.csv", {"repo": DX, "skill": KNOW, "model": "Haiku"}, "agent_minutes"), "its session length (minutes)"),
    ("rqOneCallsOutlier", "cost_per_run.csv", csv_value("cost_per_run.csv", {"repo": DX, "skill": KNOW, "model": "Haiku"}, "main_tool_calls"), "its main agent's tool calls"),
    ("rqOneWaitOutlier", "cost_per_run.csv", csv_value("cost_per_run.csv", {"repo": DX, "skill": KNOW, "model": "Haiku"}, "main_wait_calls"), "of those, calls that only wait (Monitor, or Bash starting with sleep)"),
]

# Numbers printed as money, with two decimals
MONEY = {"rqOneCostTotal", "rqOneCostPerConfirmed", "rqOneCostOutlier"}


def formatted(value, money=False):
    """How a number is printed in the paper.

    Whole counts get a thousands comma (2543 -> 2,543). Money keeps two decimals.
    Everything else (percentages, minutes) keeps exactly one decimal, also .0.
    """
    if money:
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:,.1f}"


# ---------------------------------------------------------------------------
# Tables. Each builder returns (the LaTeX, the list of its cells with sources).
# ---------------------------------------------------------------------------

SKILL_MACRO = {FULL: r"\taxorules", KNOW: r"\taxo", CTRL: r"\unguided"}


def cell(cells, table, row, column, file_name, where, field, money=False):
    """Look one cell up, remember where it came from, and return it formatted."""
    value, line = from_csv(file_name, where, field) if file_name.endswith((".csv", ".tsv")) \
        else from_json(file_name, where)
    cells.append({"table": table, "row": row, "column": column, "value": formatted(value, money),
                  "file": file_name, "line": line, "field": field})
    return formatted(value, money)


def table_runs():
    """One row per (repo, skill), one block of columns per model."""
    cells = []
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{RQ1, one run per repository, configuration and model. \textit{Listed}: units listed in Step~1."
        r" \textit{Smelly}: units with an accepted smell in Step~2, and their share of the repository's units."
        r" \textit{Confirmed / Measured}: repairs confirmed (including partial) out of the repairs we measured in Step~3."
        r" \textit{Median}: median energy saving of the confirmed repairs.}",
        r"\label{tab:rq1-runs}",
        r"\footnotesize",
        r"\begin{tabular}{@{}llrrrrrrrr@{}}",
        r"\toprule",
        r" & & \multicolumn{4}{c}{\textbf{Sonnet}} & \multicolumn{4}{c}{\textbf{Haiku}} \\",
        r"\cmidrule(lr){3-6}\cmidrule(l){7-10}",
        r"\textbf{Repository} & \textbf{Configuration} & Listed & Smelly (\%) & Confirmed / Measured & Median (\%)"
        r" & Listed & Smelly (\%) & Confirmed / Measured & Median (\%) \\",
        r"\midrule",
    ]
    for repo in REPOS:
        for i, skill in enumerate((FULL, KNOW, CTRL)):
            parts = [r"\texttt{" + repo + "}" if i == 0 else "", SKILL_MACRO[skill]]
            for model in ("Sonnet", "Haiku"):
                where = {"repo": repo, "skill": skill, "model": model}
                row = f"{repo} / {skill} / {model}"
                listed = cell(cells, "runs", row, "Listed", "step1_per_run.csv", where, "units_listed")
                smelly = cell(cells, "runs", row, "Smelly", "step2_per_run.csv", where, "smelly_units")
                share = cell(cells, "runs", row, "Smelly %", "step2_per_run.csv", where, "pct_of_repo_units")
                confirmed = cell(cells, "runs", row, "Confirmed", "step3_per_run.csv", where, "repairs_saving")
                measured = cell(cells, "runs", row, "Measured", "step3_per_run.csv", where, "repairs_measured")
                middle = cell(cells, "runs", row, "Median %", "step3_per_run.csv", where, "median_saving_pct")
                parts += [listed, f"{smelly} ({share})", f"{confirmed} / {measured}", middle]
            lines.append(" & ".join(parts) + r" \\")
        if repo != REPOS[-1]:
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines), cells


def table_together():
    """The six runs on each repository together; one column per repository."""
    cells = []
    rows = [  # (label, field, field of a percentage shown in brackets or None)
        ("Units", "units", None),
        (r"Smelly in any run (\%)", "smelly_any", "pct_smelly_any"),
        ("Smelly in all six runs", "smelly_all_6", None),
        ("Functions with a confirmed repair", "confirmed_any", None),
        (r"\quad by one configuration only", "by_1_skill", None),
        (r"\quad by two configurations", "by_2_skills", None),
        (r"\quad by all three configurations", "by_3_skills", None),
        (r"\quad only by \taxorules", "only_Taxonomy+Rules", None),
        (r"\quad only by \taxo", "only_Taxonomy", None),
        (r"\quad only by \unguided", "only_Unguided", None),
        (r"\quad with one model only", "by_1_model", None),
        (r"Median best saving (\%)", "median_best_saving_pct", None),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{RQ1, the six runs on each repository together. A function counts once, whichever runs"
        r" confirmed a repair of it; its best saving is the largest over those runs.}",
        r"\label{tab:rq1-together}",
        r"\footnotesize",
        r"\begin{tabular}{@{}lrrr@{}}",
        r"\toprule",
        " & ".join([""] + [r"\texttt{" + repo + "}" for repo in REPOS]) + r" \\",
        r"\midrule",
    ]
    for label, field, pct_field in rows:
        parts = [label]
        for repo in REPOS:
            value = cell(cells, "together", label, repo, "together_per_repo.csv", {"repo": repo}, field)
            if pct_field:
                value = value + " (" + cell(cells, "together", label + " %", repo,
                                            "together_per_repo.csv", {"repo": repo}, pct_field) + ")"
            parts.append(value)
        lines.append(" & ".join(parts) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines), cells


# The category names of the taxonomy, shortened to fit one column
SHORT_NAMES = {
    "C1": "Redundant Computation", "C2": "Call Overhead", "C3": "Iteration Patterns",
    "C4": "Control Flow", "C5": "Data Structures", "C6": "Memory Usage",
    "C7": "Algorithmic", "C8": "Missing Reuse", "C9": "External Data Access",
    "C10": "Language Primitives", "C11": "Concurrency Management", "C12": "Hardware Locality",
}


def table_categories():
    """From smells to confirmed repairs, per category, in the 12 taxonomy runs."""
    cells = []
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{RQ1, from smells to confirmed repairs, per category, over the twelve runs of \taxorules and \taxo"
        r" (category names shortened). \textit{Repairs}: repairs submitted. \textit{Per 100}: confirmed repairs per"
        r" 100 smells. \textit{Median}: median saving of the confirmed repairs.}",
        r"\label{tab:rq1-categories}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}llrrrrr@{}}",
        r"\toprule",
        r"& \textbf{Category} & Smells & Repairs & Confirmed & Per 100 & Median (\%) \\",
        r"\midrule",
    ]
    for number_ in range(1, 13):
        key = "C" + str(number_)
        where = {"id": key}
        parts = [key, SHORT_NAMES[key]]
        for column, field in (("Smells", "smells"), ("Repairs", "submitted"),
                              ("Confirmed", "confirmed"), ("Per 100", "confirmed_per_100_smells"),
                              ("Median %", "median_saving_pct")):
            if read_rows_value("categories_funnel.csv", where, field) == "":
                parts.append("--")                   # empty: no smell, or no confirmed repair
                continue
            parts.append(cell(cells, "categories", key, column, "categories_funnel.csv", where, field))
        lines.append(" & ".join(parts) + r" \\")
    lines.append(r"\midrule")
    parts = ["", "All"]
    for column, keys in (("Smells", ["smells"]), ("Repairs", ["submitted"]),
                         ("Confirmed", ["confirmed"]), ("Per 100", ["confirmed_per_100_smells"]),
                         ("Median %", ["median_saving_pct"])):
        parts.append(cell(cells, "categories", "All", column, "categories_summary.json", keys, keys[-1]))
    lines.append(" & ".join(parts) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines), cells


def read_rows_value(file_name, where, field):
    """The raw text of one cell (empty when the cell is empty)."""
    for row in read_rows(file_name):
        if matches(row, where):
            return row[field]
    raise SystemExit(f"{file_name}: no row matches {where}")


def table_repairs():
    """Verdicts of the measured repairs, by configuration, model, size, change and rule flag."""
    cells = []
    blocks = [  # (block title, file, column that names the group, [(group value, label)])
        ("Configuration", "repairs_by_skill.csv", "skill",
         [(FULL, SKILL_MACRO[FULL]), (KNOW, SKILL_MACRO[KNOW]), (CTRL, SKILL_MACRO[CTRL])]),
        ("Model", "repairs_by_model.csv", "model", [("Sonnet", "Sonnet"), ("Haiku", "Haiku")]),
        ("Lines changed", "repairs_by_size.csv", "size_group",
         [("1-2", "1--2"), ("3-6", "3--6"), ("7-15", "7--15"), ("16+", "16 or more")]),
        ("Change to the loops", "repairs_by_change.csv", "change_group",
         [("Changes the loops", "Changes the loops"),
          ("Fewer calls inside loops", "Fewer calls inside loops"),
          ("Fewer calls outside loops", "Fewer calls outside loops"),
          ("Same loops and calls", "Same loops and calls")]),
        ("Unit flagged by a static rule", "repairs_by_rule_flag.csv", "rule_flagged_unit",
         [("True", "Yes"), ("False", "No")]),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{RQ1, verdicts of the measured repairs by group. \textit{Confirmed} includes partial repairs."
        r" \textit{Median}: median saving of the confirmed repairs. Lines are counted after Python's parser has"
        r" removed comments and formatting; loops include comprehensions.}",
        r"\label{tab:rq1-repairs}",
        r"\footnotesize",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"& Measured & Confirmed (\%) & Regressed (\%) & Median (\%) \\",
        r"\midrule",
    ]

    def group_row(label, file_name, where):
        measured = cell(cells, "repairs", label, "Measured", file_name, where, "measured")
        confirmed = cell(cells, "repairs", label, "Confirmed", file_name, where, "confirmed")
        pct = cell(cells, "repairs", label, "Confirmed %", file_name, where, "pct_confirmed")
        regressed = cell(cells, "repairs", label, "Regressed", file_name, where, "regressed")
        pct_regressed = cell(cells, "repairs", label, "Regressed %", file_name, where, "pct_regressed")
        middle = cell(cells, "repairs", label, "Median %", file_name, where, "median_saving_pct")
        return f"{label} & {measured} & {confirmed} ({pct}) & {regressed} ({pct_regressed}) & {middle} \\\\"

    # The first row: all measured repairs, from repairs_summary.json
    parts = ["All repairs"]
    parts.append(cell(cells, "repairs", "All", "Measured", "repairs_summary.json", ["all", "measured"], "measured"))
    parts.append(cell(cells, "repairs", "All", "Confirmed", "repairs_summary.json", ["all", "confirmed"], "confirmed")
                 + " (" + cell(cells, "repairs", "All", "Confirmed %", "repairs_summary.json",
                               ["all", "pct_confirmed"], "pct_confirmed") + ")")
    parts.append(cell(cells, "repairs", "All", "Regressed", "repairs_summary.json", ["all", "regressed"], "regressed")
                 + " (" + cell(cells, "repairs", "All", "Regressed %", "repairs_summary.json",
                               ["all", "pct_regressed"], "pct_regressed") + ")")
    parts.append(cell(cells, "repairs", "All", "Median %", "repairs_summary.json",
                      ["all", "median_saving_pct"], "median_saving_pct"))
    lines.append(" & ".join(parts) + r" \\")

    for title, file_name, column, groups in blocks:
        lines.append(r"\midrule")
        lines.append(r"\multicolumn{5}{@{}l}{\textit{" + title + r"}} \\")
        for value, label in groups:
            where = {column: value}
            if file_name == "repairs_by_rule_flag.csv":
                where["within"] = "all"              # the overall split, not per repo/skill/model
            lines.append(group_row(r"\quad " + label, file_name, where))
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines), cells


def table_cost():
    """Cost, tokens, time, tool calls and subagents, per model and configuration."""
    cells = []
    columns = [  # (header, field, money?)
        (r"Cost (\$)", "cost_usd", True),
        (r"\$ per conf.", "usd_per_confirmed_repair", True),
        ("Session (min)", "agent_minutes", False),
        ("Model (min)", "api_minutes", False),
        ("Output (k tok.)", "output_tokens_thousands", False),
        (r"Thinking (\%)", "pct_output_thinking", False),
        ("Cache read (M tok.)", "cache_read_tokens_millions", False),
        ("Calls, main", "main_tool_calls", False),
        ("Calls, subagents", "subagent_tool_calls", False),
        ("Subagents", "subagents", False),
    ]
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{RQ1, effort of the runs as Claude Code reported it, added up over the three repositories."
        r" \textit{Cost}: Claude Code's cost of the sessions at list prices, subagents included;"
        r" \textit{\$ per conf.}: cost per confirmed repair. \textit{Session}: length of the agent's sessions;"
        r" \textit{Model}: time spent waiting for the model, subagents included. \textit{Output}: output tokens,"
        r" of which \textit{Thinking} is the share spent thinking. \textit{Calls}: tool calls by the main agent"
        r" and by its subagents.}",
        r"\label{tab:rq1-cost}",
        r"\footnotesize",
        r"\begin{tabular}{@{}ll" + "r" * len(columns) + r"@{}}",
        r"\toprule",
        r"\textbf{Model} & \textbf{Configuration} & " + " & ".join(h for h, _, _ in columns) + r" \\",
        r"\midrule",
    ]
    for model in ("Sonnet", "Haiku"):
        for i, skill in enumerate((FULL, KNOW, CTRL)):
            parts = [model if i == 0 else "", SKILL_MACRO[skill]]
            where = {"model": model, "skill": skill}
            for header, field, money in columns:
                parts.append(cell(cells, "cost", f"{model} / {skill}", header, "cost_per_skill_model.csv",
                                  where, field, money))
            lines.append(" & ".join(parts) + r" \\")
        parts = ["", "All"]
        for header, field, money in columns:
            parts.append(cell(cells, "cost", f"{model} / All", header, "cost_per_model.csv",
                              {"model": model}, field, money))
        lines.append(" & ".join(parts) + r" \\")
        if model == "Sonnet":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines), cells


TABLES = [  # (file name, builder, label)
    ("table_runs.tex", table_runs, "tab:rq1-runs"),
    ("table_together.tex", table_together, "tab:rq1-together"),
    ("table_categories.tex", table_categories, "tab:rq1-categories"),
    ("table_repairs.tex", table_repairs, "tab:rq1-repairs"),
    ("table_cost.tex", table_cost, "tab:rq1-cost"),
]


def main():
    LATEX.mkdir(parents=True, exist_ok=True)
    PAPER.mkdir(parents=True, exist_ok=True)

    tex = ["% Generated by analysis/rq1_latex.py. Do not edit by hand.",
           "% Where each number comes from: analysis/output/rq1/latex/numbers.md"]
    ledger = ["# RQ1 numbers: where each one comes from",
              "",
              "Generated by `analysis/rq1_latex.py`. Every number in the RQ1 text is listed",
              "here with its value, the file it is read from (in `analysis/output/rq1/`, or",
              "`analysis/output/repo_stats.tsv`), the line in that file, the script that wrote",
              "the file, and what it means. The table cells follow at the end.",
              "",
              "| Command | Value | File | Line | Written by | What it is |",
              "|---|---|---|---|---|---|"]
    as_json = {}
    for name, file_name, find, meaning in NUMBERS:
        value, line = find()                         # look the number up
        shown = formatted(value, name in MONEY)
        tex.append(f"\\newcommand{{\\{name}}}{{{shown}}}")
        ledger.append(f"| `\\{name}` | {shown} | `{file_name}` | {line} | {MADE_BY[file_name]} | {meaning} |")
        as_json[name] = {"value": shown, "file": file_name, "line": line,
                         "made_by": MADE_BY[file_name], "meaning": meaning}

    count = 0
    for file_name, build, label in TABLES:
        table, cells = build()
        header = ["% Generated by analysis/rq1_latex.py. Do not edit by hand;",
                  "% the source of every cell is in analysis/output/rq1/latex/numbers.md."]
        (LATEX / file_name).write_text("\n".join(header) + "\n" + table + "\n")
        ledger += ["", f"## Table {label} (`{file_name}`)", "",
                   "| Row | Column | Value | File | Line | Field | Written by |",
                   "|---|---|---|---|---|---|---|"]
        for c in cells:
            ledger.append(f"| {c['row']} | {c['column']} | {c['value']} | `{c['file']}` | {c['line']} | "
                          f"`{c['field']}` | {MADE_BY[c['file']]} |")
        count = count + len(cells)

    (LATEX / "numbers.tex").write_text("\n".join(tex) + "\n")
    (LATEX / "numbers.md").write_text("\n".join(ledger) + "\n")
    (LATEX / "numbers.json").write_text(json.dumps(as_json, indent=2) + "\n")
    for name in ["numbers.tex", "numbers.md", "numbers.json"] + [t[0] for t in TABLES]:
        shutil.copy(LATEX / name, PAPER / name)     # the copy the paper reads
    print(f"wrote {len(NUMBERS)} numbers and {count} table cells to {LATEX} and {PAPER}")


if __name__ == "__main__":
    main()
