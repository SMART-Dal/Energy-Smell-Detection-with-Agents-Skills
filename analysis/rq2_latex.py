"""Every number the RQ2 text and tables use, taken from the output files.

Like rq1_latex.py, this script computes nothing new: it looks numbers up in the
files that rq2_root_causes.py and rq2_strategies.py wrote (in output/rq2/), and
writes, to output/rq2/latex/:

  numbers.tex                    one LaTeX command per number (\\rqTwo...)
  numbers.json                   the same numbers with their file, line and meaning
  numbers.md                     the ledger: every number and every table cell
  table_rq2_root_causes.tex      the root causes with at least 3 measured instances
  table_rq2_categories.tex       the twelve categories, counted by instance
  table_rq2_strategies.tex       how each of those root causes was repaired

and copies them to temp_main_paper/results/generated/ with an "rq2_" prefix on
the numbers files.

Run after rq2_strategies.py:  python3 analysis/rq2_latex.py
"""

import json
import shutil

from common import OUTPUT_DIR, ROOT
from rq1_latex import csv_max, csv_min, csv_value, formatted, from_csv, json_value, read_rows

RQ2 = OUTPUT_DIR / "rq2"
LATEX = RQ2 / "latex"                                  # where this script writes
PAPER = ROOT / "temp_main_paper" / "results" / "generated"

MADE_BY = {
    "rq2/summary.json": "analysis/rq2_root_causes.py, main()",
    "rq2/root_causes.csv": "analysis/rq2_root_causes.py, summary_of()",
    "rq2/root_causes_table.csv": "analysis/rq2_root_causes.py, summary_of()",
    "rq2/categories.csv": "analysis/rq2_root_causes.py, summary_of()",
    "rq2/strategies.csv": "analysis/rq2_strategies.py, describe() (strategies hand-coded in rq2_strategy_coding.csv)",
    "rq2/strategies_by_root_cause.csv": "analysis/rq2_strategies.py, main()",
    "rq2/strategies_overall.csv": "analysis/rq2_strategies.py, describe()",
    "rq2/strategies_summary.json": "analysis/rq2_strategies.py, main()",
    "step2_summary.json": "analysis/rq1_step2.py, main()",
    "rq2/agreement.csv": "analysis/rq2_agreement.py, compare() and shares()",
}


def whole(find):
    """A finder whose value is printed without decimals when it is a whole number (2.0 -> 2)."""
    def found():
        value, line = find()
        return (int(value) if value == int(value) else value), line
    return found


def strategy_saving(cause, strategy):
    """The median saving of one strategy of one root cause, from strategies.csv."""
    return csv_value("rq2/strategies.csv", {"root_cause": cause, "strategy": strategy},
                     "median_saving_confirmed_pct")


S = "rq2/summary.json"
T = "rq2/strategies_summary.json"
NUMBERS = [
    # --- counting by instance ---
    ("rqTwoSmells", "step2_summary.json", json_value("step2_summary.json", "smells_in_taxonomy_runs"), "accepted smells in the 12 taxonomy runs (counted per run)"),
    ("rqTwoInstances", S, json_value(S, "instances"), "instances: distinct (unit, root cause) pairs among those smells"),
    ("rqTwoFoundByTwo", S, json_value(S, "found_by_2_or_more_runs"), "instances found by two or more runs"),
    ("rqTwoRepaired", S, json_value(S, "repaired"), "instances with at least one submitted repair"),
    ("rqTwoMeasured", S, json_value(S, "measured"), "instances with at least one measured repair"),
    ("rqTwoConfirmed", S, json_value(S, "confirmed"), "instances with at least one confirmed (or partial) repair"),
    ("rqTwoMultiMeasured", S, json_value(S, "instances_with_2_or_more_measured_repairs"), "instances with two or more measured repairs"),
    ("rqTwoDisagree", S, json_value(S, "instances_whose_repairs_disagree"), "of those, instances where some repairs were confirmed and some not"),
    ("rqTwoRootCausesFound", S, json_value(S, "root_causes_found"), "root causes with at least one instance"),
    ("rqTwoRootCausesConfirmed", S, json_value(S, "root_causes_confirmed"), "root causes with at least one confirmed instance"),
    ("rqTwoCategoriesFound", S, json_value(S, "categories_found"), "categories with at least one instance"),
    ("rqTwoMultiConfirmedPct", S, json_value(S, "pct_confirmed_measured_2_or_more"), "confirmed share of instances with two or more measured repairs (%)"),
    ("rqTwoSingleConfirmedPct", S, json_value(S, "pct_confirmed_measured_once"), "confirmed share of instances with one measured repair (%)"),
    ("rqTwoCTenRepairedPct", "rq2/categories.csv", csv_value("rq2/categories.csv", {"category": "C10"}, "pct_repaired"), "share of C10 instances the agents repaired (%)"),
    ("rqTwoAllRepairedPct", "rq2/categories.csv", csv_value("rq2/categories.csv", {"category": "All"}, "pct_repaired"), "share of all instances the agents repaired (%)"),
    ("rqTwoCTenMeasuredConfirmed", "rq2/categories.csv", csv_value("rq2/categories.csv", {"category": "C10"}, "pct_measured_confirmed"), "share of measured C10 instances that are confirmed (%)"),
    ("rqTwoCNineConfirmed", "rq2/categories.csv", csv_value("rq2/categories.csv", {"category": "C9"}, "confirmed"), "confirmed C9 instances"),
    ("rqTwoCNineMeasured", "rq2/categories.csv", csv_value("rq2/categories.csv", {"category": "C9"}, "measured"), "measured C9 instances"),
    ("rqTwoCElevenInstances", "rq2/categories.csv", csv_value("rq2/categories.csv", {"category": "C11"}, "instances"), "instances of category C11"),
    ("rqTwoCElevenSFive", "rq2/root_causes.csv", csv_value("rq2/root_causes.csv", {"root_cause": "C11.S5"}, "instances"), "of those, Missed Parallelism Opportunities (C11.S5)"),
    ("rqTwoCEightSFourInstances", "rq2/root_causes.csv", csv_value("rq2/root_causes.csv", {"root_cause": "C8.S4"}, "instances"), "instances of C8.S4 (Redundant Data Fetching)"),
    ("rqTwoCEightSFourDx", "rq2/root_causes.csv", csv_value("rq2/root_causes.csv", {"root_cause": "C8.S4"}, "instances_dx-toolkit"), "of those, in dx-toolkit"),
    ("rqTwoCEightSFourRepaired", "rq2/root_causes.csv", csv_value("rq2/root_causes.csv", {"root_cause": "C8.S4"}, "repaired"), "C8.S4 instances with a submitted repair"),

    # --- agreement between runs ---
    ("rqTwoAgreeRootCause", "rq2/agreement.csv", csv_value("rq2/agreement.csv", {"comparison": "Any two taxonomy runs"}, "pct_same_root_cause"), "of the units two taxonomy runs both found smelly, share with a root cause in common (%)"),
    ("rqTwoAgreeCategory", "rq2/agreement.csv", csv_value("rq2/agreement.csv", {"comparison": "Any two taxonomy runs"}, "pct_same_category"), "the same, with a category in common (%)"),

    # --- repair strategies ---
    ("rqTwoEditsCoded", T, json_value(T, "edits_coded"), "distinct edits read and coded"),
    ("rqTwoStrategyCauses", T, json_value(T, "root_causes"), "root causes whose edits were coded"),
    ("rqTwoStrategies", T, json_value(T, "distinct_strategies"), "distinct strategies"),
    ("rqTwoSharedStrategies", T, json_value(T, "strategies_used_for_2_or_more_root_causes"), "strategies used for two or more root causes"),
    ("rqTwoOneStrategyCauses", T, json_value(T, "root_causes_with_one_strategy"), "root causes repaired with a single strategy"),
    ("rqTwoTwoStrategyInstances", T, json_value(T, "instances_with_2_strategies"), "instances repaired with two different strategies"),
    ("rqTwoLinesMin", "rq2/strategies_by_root_cause.csv", whole(csv_min("rq2/strategies_by_root_cause.csv", "median_lines_changed")), "smallest median of lines changed, over the coded root causes"),
    ("rqTwoLinesMax", "rq2/strategies_by_root_cause.csv", whole(csv_max("rq2/strategies_by_root_cause.csv", "median_lines_changed")), "largest median of lines changed, over the coded root causes"),
    ("rqTwoReuseCallSaving", "rq2/strategies.csv", strategy_saving("C1.S4", "Reuse a call's result"), "C1.S4, reuse a call's result: median saving (%)"),
    ("rqTwoFastPathSaving", "rq2/strategies.csv", strategy_saving("C1.S4", "Add a fast path that skips the work"), "C1.S4, add a fast path: median saving (%)"),
    ("rqTwoHoistSaving", "rq2/strategies.csv", strategy_saving("C3.S2", "Move invariant work out of the loop"), "C3.S2, move invariant work out of the loop: median saving (%)"),
    ("rqTwoUnswitchSaving", "rq2/strategies.csv", strategy_saving("C3.S2", "Move an invariant test out of the loop"), "C3.S2, move an invariant test out of the loop: median saving (%)"),
]


def cell(cells, table, row, column, file_name, where, field):
    """Look one cell up, remember where it came from, and return it formatted ("--" if empty)."""
    for r in read_rows(file_name):
        if all(r[k] == v for k, v in where.items()) and r[field] == "":
            return "--"                                  # an empty cell: nothing to report
    value, line = from_csv(file_name, where, field)
    cells.append({"table": table, "row": row, "column": column, "value": formatted(value),
                  "file": file_name, "line": line, "field": field})
    return formatted(value)


def table_root_causes():
    """One row per root cause with at least 3 measured instances."""
    cells = []
    f = "rq2/root_causes_table.csv"
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{RQ2, root causes with at least three measured instances, most frequent first. An instance is one root"
        r" cause in one unit, counted once however many runs found or repaired it. \textit{Found}: instances, and those"
        r" found by two or more runs. \textit{Confirmed / Measured}: instances with a confirmed (or partial) repair, out of"
        r" those with a measured repair. \textit{Median}: median of each confirmed instance's best saving.}",
        r"\label{tab:rq2-root-causes}",
        r"\footnotesize",
        r"\begin{tabular}{@{}llrrrrr@{}}",
        r"\toprule",
        r"& \textbf{Root cause} & Found & Found by $\geq$2 runs & Repaired & Confirmed / Measured & Median (\%) \\",
        r"\midrule",
    ]
    for row in read_rows(f):
        cause = row["root_cause"]
        where = {"root_cause": cause}
        parts = [cause, row["name"]]
        parts.append(cell(cells, "rq2-root-causes", cause, "Found", f, where, "instances"))
        parts.append(cell(cells, "rq2-root-causes", cause, "Found by 2+", f, where, "found_by_2_or_more_runs"))
        parts.append(cell(cells, "rq2-root-causes", cause, "Repaired", f, where, "repaired"))
        parts.append(cell(cells, "rq2-root-causes", cause, "Confirmed", f, where, "confirmed") + " / "
                     + cell(cells, "rq2-root-causes", cause, "Measured", f, where, "measured"))
        parts.append(cell(cells, "rq2-root-causes", cause, "Median", f, where, "median_best_saving_pct"))
        lines.append(" & ".join(parts) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines), cells


# The category names of the taxonomy, shortened to fit one column
SHORT_NAMES = {
    "C1": "Redundant Computation", "C2": "Call Overhead", "C3": "Iteration Patterns",
    "C4": "Control Flow", "C5": "Data Structures", "C6": "Memory Usage",
    "C7": "Algorithmic", "C8": "Missing Reuse", "C9": "External Data Access",
    "C10": "Language Primitives", "C11": "Concurrency Management", "C12": "Hardware Locality",
    "All": "All",
}


def table_categories():
    """One row per category, counted by instance."""
    cells = []
    f = "rq2/categories.csv"
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{RQ2, instances per category (names shortened). \textit{Per 100}: confirmed instances per 100 instances"
        r" found. \textit{Median}: median of each confirmed instance's best saving.}",
        r"\label{tab:rq2-categories}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabular}{@{}llrrrrr@{}}",
        r"\toprule",
        r"& \textbf{Category} & Found & Repaired & Conf. / Meas. & Per 100 & Median (\%) \\",
        r"\midrule",
    ]
    for row in read_rows(f):
        key = row["category"]
        where = {"category": key}
        if key == "All":
            lines.append(r"\midrule")
        parts = ["" if key == "All" else key, SHORT_NAMES[key]]
        parts.append(cell(cells, "rq2-categories", key, "Found", f, where, "instances"))
        parts.append(cell(cells, "rq2-categories", key, "Repaired", f, where, "repaired"))
        parts.append(cell(cells, "rq2-categories", key, "Confirmed", f, where, "confirmed") + " / "
                     + cell(cells, "rq2-categories", key, "Measured", f, where, "measured"))
        parts.append(cell(cells, "rq2-categories", key, "Per 100", f, where, "confirmed_per_100_instances"))
        parts.append(cell(cells, "rq2-categories", key, "Median", f, where, "median_best_saving_pct"))
        lines.append(" & ".join(parts) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines), cells


def table_strategies():
    """For each root cause of the RQ2 table: its strategies, with instances, confirmed ones and median saving."""
    cells = []
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{RQ2, how agents repaired each root cause of Table~\ref{tab:rq2-root-causes}, named by reading every"
        r" distinct edit. For each strategy: the measured instances repaired with it, how many of them were confirmed,"
        r" and the median best saving of the confirmed ones (-- when none was). \textit{Lines}: median lines changed,"
        r" after Python's parser has removed comments, docstrings and formatting.}",
        r"\label{tab:rq2-strategies}",
        r"\footnotesize",
        r"\begin{tabular}{@{}lrp{12.2cm}r@{}}",
        r"\toprule",
        r"\textbf{Root cause} & Measured & \textbf{Strategies} (instances, confirmed; median saving \%) & Lines \\",
        r"\midrule",
    ]
    strategies = read_rows("rq2/strategies.csv")
    for row in read_rows("rq2/root_causes_table.csv"):
        cause = row["root_cause"]
        f = "rq2/strategies_by_root_cause.csv"
        measured = cell(cells, "rq2-strategies", cause, "Measured", f, {"root_cause": cause}, "measured_instances")
        median_lines = cell(cells, "rq2-strategies", cause, "Lines", f, {"root_cause": cause}, "median_lines_changed")
        items = []
        for s in strategies:                             # in the order rq2_strategies.py wrote them
            if s["root_cause"] != cause:
                continue
            where = {"root_cause": cause, "strategy": s["strategy"]}
            n = cell(cells, "rq2-strategies", cause, s["strategy"] + " instances", "rq2/strategies.csv",
                     where, "instances")
            confirmed = cell(cells, "rq2-strategies", cause, s["strategy"] + " confirmed", "rq2/strategies.csv",
                             where, "confirmed")
            saving = cell(cells, "rq2-strategies", cause, s["strategy"] + " saving", "rq2/strategies.csv",
                          where, "median_saving_confirmed_pct")
            items.append(s["strategy"].replace("_", r"\_") + f" ({n}, {confirmed}; {saving})")
        lines.append(f"{cause} & {measured} & " + "; ".join(items) + f" & {median_lines} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    return "\n".join(lines), cells


def table_agreement():
    """Agreement between pairs of taxonomy runs, the three repositories together."""
    cells = []
    f = "rq2/agreement.csv"
    labels = [  # (comparison in agreement.csv, label in the table)
        ("Sonnet vs Haiku, Taxonomy+Rules", r"Sonnet vs Haiku, \taxorules"),
        ("Sonnet vs Haiku, Taxonomy", r"Sonnet vs Haiku, \taxo"),
        ("Taxonomy+Rules vs Taxonomy, Sonnet", r"\taxorules vs \taxo, Sonnet"),
        ("Taxonomy+Rules vs Taxonomy, Haiku", r"\taxorules vs \taxo, Haiku"),
        ("Any two taxonomy runs", "Any two runs"),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{RQ2, agreement between two runs on the same repository, the three repositories together."
        r" \textit{Units} and \textit{Instances}: smelly units and (unit, root cause) pairs found by both runs, as a"
        r" share of those found by either (Jaccard). \textit{Same root cause} and \textit{Same category}: of the units"
        r" both runs found smelly, those given at least one root cause (category) in common.}",
        r"\label{tab:rq2-agreement}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"& Units (\%) & Instances (\%) & Same root cause (\%) & Same category (\%) \\",
        r"\midrule",
    ]
    for comparison, label in labels:
        where = {"comparison": comparison}
        if comparison == "Any two taxonomy runs":
            lines.append(r"\midrule")
        parts = [label]
        for column, field in (("Units", "units_jaccard_pct"), ("Instances", "instances_jaccard_pct"),
                              ("Same root cause", "pct_same_root_cause"),
                              ("Same category", "pct_same_category")):
            parts.append(cell(cells, "rq2-agreement", comparison, column, f, where, field))
        lines.append(" & ".join(parts) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines), cells


TABLES = [
    ("table_rq2_root_causes.tex", table_root_causes, "tab:rq2-root-causes"),
    ("table_rq2_categories.tex", table_categories, "tab:rq2-categories"),
    ("table_rq2_strategies.tex", table_strategies, "tab:rq2-strategies"),
    ("table_rq2_agreement.tex", table_agreement, "tab:rq2-agreement"),
]


def main():
    LATEX.mkdir(parents=True, exist_ok=True)
    tex = ["% Generated by analysis/rq2_latex.py. Do not edit by hand."]
    ledger = ["# RQ2 numbers: where each one comes from", "",
              "Generated by `analysis/rq2_latex.py`. Files are under `analysis/output/`.", "",
              "| Command | Value | File | Line | Written by | What it is |", "|---|---|---|---|---|---|"]
    as_json = {}
    for name, file_name, find, meaning in NUMBERS:
        value, line = find()
        shown = formatted(value)
        tex.append(f"\\newcommand{{\\{name}}}{{{shown}}}")
        ledger.append(f"| `\\{name}` | {shown} | `{file_name}` | {line} | {MADE_BY[file_name]} | {meaning} |")
        as_json[name] = {"value": shown, "file": file_name, "line": line,
                         "made_by": MADE_BY[file_name], "meaning": meaning}
    count = 0
    for file_name, build, label in TABLES:
        table, cells = build()
        (LATEX / file_name).write_text("% Generated by analysis/rq2_latex.py. Do not edit by hand;\n"
                                       "% the source of every cell is in rq2_numbers.md.\n" + table + "\n")
        ledger += ["", f"## Table {label} (`{file_name}`)", "",
                   "| Row | Column | Value | File | Line | Field |", "|---|---|---|---|---|---|"]
        for c in cells:
            ledger.append(f"| {c['row']} | {c['column']} | {c['value']} | `{c['file']}` | {c['line']} | `{c['field']}` |")
        count = count + len(cells)
    (LATEX / "numbers.tex").write_text("\n".join(tex) + "\n")
    (LATEX / "numbers.md").write_text("\n".join(ledger) + "\n")
    (LATEX / "numbers.json").write_text(json.dumps(as_json, indent=2) + "\n")
    PAPER.mkdir(parents=True, exist_ok=True)
    for name in ("numbers.tex", "numbers.md", "numbers.json"):
        shutil.copy(LATEX / name, PAPER / ("rq2_" + name))
    for file_name, _, _ in TABLES:
        shutil.copy(LATEX / file_name, PAPER / file_name)
    print(f"wrote {len(NUMBERS)} numbers and {count} table cells to {LATEX} and {PAPER}")


if __name__ == "__main__":
    main()
