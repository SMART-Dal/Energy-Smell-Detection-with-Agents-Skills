"""RQ1, the repairs themselves: how large they are, what they change, and where.

For every repair we MEASURED (verdict confirmed, partial, mixed, regressed or
negligible), this script compares the repaired function with the original one
in the untouched repository, and asks three questions:

  1. Size: how many lines did the repair change?
     Both versions are first rewritten by Python itself (ast.unparse), which
     drops comments, blank lines and formatting. So a line counts only when the
     code on it changed. "Lines changed" = lines removed + lines added.

  2. Change: what did the repair do to the loops? From Python's own parse of
     both versions we count, in each version:
       loops            for, while, and every "for" inside a comprehension
       deepest          how many loops sit inside each other at the deepest point
       calls_in_loops   function calls that run once per iteration of some loop
       calls            all function calls
     and put the repair in the first group that fits:
       "Changes the loops"         a different number of loops, or a different
                                   deepest nesting (e.g. a search loop replaced
                                   by a set lookup, or a loop by a built-in)
       "Fewer calls inside loops"  the same loops, with fewer calls running in
                                   them (e.g. work moved out of a loop)
       "Fewer calls outside loops" the same loops and the same calls inside
                                   them, fewer calls elsewhere (e.g. an unused
                                   file read deleted)
       "Same loops and calls"      none of the above (e.g. one operation swapped
                                   for a cheaper one, or a list for a set)

  3. Rules: does a static rule flag the repaired unit (rules.json)? The rules
     ran on the untouched repository in every skill, but only Taxonomy+Rules
     showed them to the agent.

Reads:
  review/results.jsonl       our verdict and saving of each repair (never the agent's)
  review/submissions.jsonl   the code of each repair ("changed": {unit: code})
  rules.json                 the units a static rule flags
  ~/energy-exp/pristine/<repo>/   the untouched repositories, at the commit every
                                  run started from (checked against run.json)

Writes to analysis/output/rq1/:
  repairs_per_repair.csv     one row per measured repair, with everything above
  repairs_by_size.csv        verdicts by lines changed (1-2, 3-6, 7-15, 16 or more)
  repairs_by_change.csv      verdicts by change group
  repairs_by_rule_flag.csv   verdicts for units a rule flags and units it does not,
                             overall and per repository, skill, model and category
  repairs_by_skill.csv       verdicts, size and change group of each skill's repairs
  repairs_by_model.csv       verdicts, size and change group of each model's repairs
  repairs_summary.json       the totals and the confidence intervals (see bootstrap.py)

Run:  python3 analysis/rq1_repairs.py
"""

import ast
import difflib
import os
import subprocess
import textwrap
from pathlib import Path

from bootstrap import run_bootstrap
from common import (MEASURED, MODEL_NAMES, OUTPUT_DIR, REPOS, SAVES, SKILL_NAMES,
                    all_runs, category_of, median, percent, read_json, read_jsonl,
                    run_folder, write_csv, write_json)

OUT = OUTPUT_DIR / "rq1"   # where this script writes

# The untouched repositories, the same copies every run started from
PRISTINE = Path(os.environ.get("ENERGY_EXP", Path.home() / "energy-exp")) / "pristine"

# The size groups: (name, fewest lines, most lines)
SIZES = [("1-2", 1, 2), ("3-6", 3, 6), ("7-15", 7, 15), ("16+", 16, 10**9)]

# The change groups, in the order the table shows them
CHANGES = ["Changes the loops", "Fewer calls inside loops",
           "Fewer calls outside loops", "Same loops and calls"]

# The comparisons we give an interval for. Three comparisons share the usual
# 5% error, so each interval is 100 - 5/3 = 98.3% wide (Bonferroni).
COMPARISONS = 3
COMPARISON_LEVEL = 100.0 - 5.0 / COMPARISONS


# ---------------------------------------------------------------------------
# Finding the original code
# ---------------------------------------------------------------------------

def check_pristine_commit(repo):
    """Stop if the pristine clone is not at the commit the runs analyzed."""
    wanted = read_json(run_folder(repo, "full", "sonnet") / "run.json")["repo_commit"]
    found = subprocess.run(["git", "-C", str(PRISTINE / repo), "rev-parse", "HEAD"],
                           capture_output=True, text=True).stdout.strip()
    if found != wanted:
        raise SystemExit(f"{repo}: pristine clone is at {found}, the runs used {wanted}")


def original_function(repo, unit):
    """The parsed function `unit` ('path.py::Class.method') in the untouched repository.

    Returns None when the repository has no such function (a new helper).
    """
    path, name = unit.split("::")                       # 'a/b.py', 'Class.method'
    tree = ast.parse((PRISTINE / repo / path).read_text())
    node = tree
    for part in name.split("."):                        # walk down: Class, then method
        found = None
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) \
                    and child.name == part:
                found = child                           # the last definition wins, as in Python
        if found is None:
            return None
        node = found
    return node


def repaired_function(code):
    """The parsed function from the code the agent submitted."""
    module = ast.parse(textwrap.dedent(code))           # dedent: a method may be indented
    return module.body[0]                               # the submission is one function


# ---------------------------------------------------------------------------
# 1. Size
# ---------------------------------------------------------------------------

def normalized_lines(function):
    """The function as Python rewrites it: no comments, no blank lines, one style.

    Decorators are left out, because some submissions include them and others
    do not; they are never what a repair changes.
    """
    function.decorator_list = []
    return ast.unparse(function).splitlines()


def lines_changed(before, after):
    """Lines removed plus lines added between two lists of lines."""
    changed = 0
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":                              # 'replace', 'delete' or 'insert'
            changed = changed + (i2 - i1) + (j2 - j1)   # removed lines + added lines
    return changed


def size_group(lines):
    """The name of the size group a number of changed lines falls in."""
    for name, fewest, most in SIZES:
        if fewest <= lines <= most:
            return name
    return "0"                                          # nothing changed (does not happen)


# ---------------------------------------------------------------------------
# 2. What the repair does to the loops
# ---------------------------------------------------------------------------

def loop_features(function):
    """Count loops, the deepest nesting, calls inside loops and all calls."""
    counts = {"loops": 0, "deepest": 0, "calls_in_loops": 0, "calls": 0}

    def visit(node, depth):
        # `depth` is how many loops are around this node
        if isinstance(node, (ast.For, ast.AsyncFor)):
            counts["loops"] += 1
            counts["deepest"] = max(counts["deepest"], depth + 1)
            visit(node.iter, depth)                     # evaluated once, before the loop
            for statement in node.body:                 # runs once per iteration
                visit(statement, depth + 1)
            for statement in node.orelse:               # the 'else:' runs once, after
                visit(statement, depth)
            return
        if isinstance(node, ast.While):
            counts["loops"] += 1
            counts["deepest"] = max(counts["deepest"], depth + 1)
            visit(node.test, depth + 1)                 # the test runs every iteration
            for statement in node.body:
                visit(statement, depth + 1)
            for statement in node.orelse:
                visit(statement, depth)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            # [elt for a in A if c for b in B]: each "for" is one more loop level
            levels = len(node.generators)
            for i, generator in enumerate(node.generators):
                counts["loops"] += 1
                visit(generator.iter, depth + i)        # A is outside, B is inside the first loop
                for condition in generator.ifs:
                    visit(condition, depth + i + 1)
            counts["deepest"] = max(counts["deepest"], depth + levels)
            if isinstance(node, ast.DictComp):
                visit(node.key, depth + levels)
                visit(node.value, depth + levels)
            else:
                visit(node.elt, depth + levels)
            return
        if isinstance(node, ast.Call):
            counts["calls"] += 1
            if depth > 0:                               # inside at least one loop
                counts["calls_in_loops"] += 1
        for child in ast.iter_child_nodes(node):        # everything else: look inside
            visit(child, depth)

    for statement in function.body:                     # the body of the function
        visit(statement, 0)
    return counts


def change_group(before, after):
    """The first change group that fits, from the counts of both versions."""
    if after["loops"] != before["loops"] or after["deepest"] != before["deepest"]:
        return "Changes the loops"
    if after["calls_in_loops"] < before["calls_in_loops"]:
        return "Fewer calls inside loops"
    if after["calls"] < before["calls"]:
        return "Fewer calls outside loops"
    return "Same loops and calls"


# ---------------------------------------------------------------------------
# One row per measured repair
# ---------------------------------------------------------------------------

def rule_flagged_units(repo):
    """The units a static rule flags. rules.json is the same in all six runs of a repository."""
    rules = read_json(run_folder(repo, "full", "sonnet") / "rules.json")
    units = set()
    for entry in rules["units"]:
        units.add(entry["unit"])
    return units


def repair_rows():
    """One row per measured repair of the 18 runs."""
    flagged = {}
    for repo in REPOS:
        check_pristine_commit(repo)
        flagged[repo] = rule_flagged_units(repo)

    rows = []
    for repo, skill, model in all_runs():
        folder = run_folder(repo, skill, model)
        code_of = {}                                    # {repair id: {unit: code}}
        for submission in read_jsonl(folder / "review" / "submissions.jsonl"):
            code_of[submission["id"]] = submission["changed"]

        for repair in read_jsonl(folder / "review" / "results.jsonl"):
            if repair["status"] not in MEASURED:
                continue                                # only repairs we measured
            changed_units = code_of[repair["id"]]

            # Size: add up the changed lines of every function the repair touches
            lines = 0
            for unit, code in changed_units.items():
                after = normalized_lines(repaired_function(code))
                original = original_function(repo, unit)
                if original is None:                    # a new function: all of it is added
                    lines = lines + len(after)
                else:
                    lines = lines + lines_changed(normalized_lines(original), after)

            # Change group: from the repaired unit itself
            before = loop_features(original_function(repo, repair["unit"]))
            after = loop_features(repaired_function(changed_units[repair["unit"]]))

            row = {}
            row["repo"] = repo
            row["skill"] = SKILL_NAMES[skill]
            row["model"] = MODEL_NAMES[model]
            row["repair"] = repair["id"]
            row["unit"] = repair["unit"]
            row["root_cause"] = repair.get("root_cause") or ""     # empty in Unguided
            row["category"] = category_of(row["root_cause"]) if row["root_cause"] else ""
            row["verdict"] = repair["status"]
            row["confirmed"] = repair["status"] in SAVES      # confirmed or partial
            row["saving_pct"] = round(repair["mean_saving_pct"], 1)
            row["functions_changed"] = len(changed_units)
            row["lines_changed"] = lines
            row["size_group"] = size_group(lines)
            row["change_group"] = change_group(before, after)
            row["rule_flagged_unit"] = repair["unit"] in flagged[repo]
            for name in ("loops", "deepest", "calls_in_loops", "calls"):
                row[name + "_before"] = before[name]
                row[name + "_after"] = after[name]
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def outcome(rows):
    """Verdict counts and savings of a group of repairs, as one dictionary."""
    savings = []                                        # savings of the confirmed repairs
    regressed = 0
    negligible = 0
    for row in rows:
        if row["confirmed"]:
            savings.append(row["saving_pct"])
        if row["verdict"] == "regressed":
            regressed = regressed + 1
        if row["verdict"] == "negligible":
            negligible = negligible + 1
    at_least_half = 0
    for saving in savings:
        if saving >= 50:
            at_least_half = at_least_half + 1
    result = {}
    result["measured"] = len(rows)
    result["confirmed"] = len(savings)
    result["pct_confirmed"] = percent(len(savings), len(rows))
    result["regressed"] = regressed
    result["pct_regressed"] = percent(regressed, len(rows))
    result["negligible"] = negligible
    result["median_saving_pct"] = round(median(savings), 1) if savings else None
    result["confirmed_at_least_50pct"] = at_least_half
    return result


def rows_where(rows, column, value):
    """The rows whose `column` has `value`."""
    kept = []
    for row in rows:
        if row[column] == value:
            kept.append(row)
    return kept


def grouped_table(rows, column, values):
    """One outcome() row per value of `column`, in the given order."""
    table = []
    for value in values:
        line = {column: value}
        line.update(outcome(rows_where(rows, column, value)))
        table.append(line)
    return table


def rule_flag_table(rows):
    """Flagged against unflagged units, overall and within each repository, skill and model."""
    table = []
    splits = [("all", "all")]
    for repo in REPOS:
        splits.append(("repo", repo))
    for skill_name in SKILL_NAMES.values():
        splits.append(("skill", skill_name))
    for model_name in MODEL_NAMES.values():
        splits.append(("model", model_name))
    for number in range(1, 13):                         # categories (taxonomy skills only)
        splits.append(("category", "C" + str(number)))
    for column, value in splits:
        if column == "all":
            subset = rows
        else:
            subset = rows_where(rows, column, value)
        if not subset:                                  # e.g. a category with no measured repair
            continue
        for flagged in (True, False):
            line = {"within": column, "value": value, "rule_flagged_unit": flagged}
            line.update(outcome(rows_where(subset, "rule_flagged_unit", flagged)))
            table.append(line)
    return table


def profile_table(rows, column, values):
    """For each skill (or model): its verdicts, how large its repairs are, and their change groups."""
    table = []
    for value in values:
        subset = rows_where(rows, column, value)
        lines = []
        small = 0
        for row in subset:
            lines.append(row["lines_changed"])
            if row["size_group"] == "1-2":
                small = small + 1
        line = {column: value}
        line.update(outcome(subset))
        line["median_lines_changed"] = median(lines)
        line["repairs_1_2_lines"] = small
        line["pct_1_2_lines"] = percent(small, len(subset))
        for change in CHANGES:
            count = len(rows_where(subset, "change_group", change))
            line["pct_" + change.lower().replace(" ", "_")] = percent(count, len(subset))
        table.append(line)
    return table


# ---------------------------------------------------------------------------
# Statistics for the bootstrap (each takes a list of repair rows)
# ---------------------------------------------------------------------------

def pct_confirmed(rows):
    """Share of the repairs that are confirmed (or partial), in percent."""
    if not rows:
        return None
    return outcome(rows)["pct_confirmed"]


def median_confirmed_saving(rows):
    """Median saving of the confirmed repairs."""
    return outcome(rows)["median_saving_pct"]


def difference(statistic, column, first, second):
    """A statistic that is (statistic on rows with column == first) minus (... == second)."""
    def compute(rows):
        a = statistic(rows_where(rows, column, first))
        b = statistic(rows_where(rows, column, second))
        if a is None or b is None:
            return None
        return a - b
    return compute


def interval(rows_by_run, statistic, level):
    """run_bootstrap(), rounded, as a dictionary."""
    value, low, high = run_bootstrap(rows_by_run, statistic, level)
    return {"value": round(value, 1), "low": round(low, 1), "high": round(high, 1),
            "level_pct": round(level, 2)}


def main():
    rows = repair_rows()
    write_csv(rows, OUT / "repairs_per_repair.csv")

    by_size = grouped_table(rows, "size_group", [name for name, _, _ in SIZES])
    by_change = grouped_table(rows, "change_group", CHANGES)
    by_flag = rule_flag_table(rows)
    by_skill = profile_table(rows, "skill", list(SKILL_NAMES.values()))
    by_model = profile_table(rows, "model", list(MODEL_NAMES.values()))
    write_csv(by_size, OUT / "repairs_by_size.csv")
    write_csv(by_change, OUT / "repairs_by_change.csv")
    write_csv(by_flag, OUT / "repairs_by_rule_flag.csv")
    write_csv(by_skill, OUT / "repairs_by_skill.csv")
    write_csv(by_model, OUT / "repairs_by_model.csv")

    # Group the repairs by run, for the bootstrap. Two helper columns mark the
    # two halves of the comparisons that are not already a column.
    rows_by_run = {}
    for row in rows:
        row["small"] = row["size_group"] == "1-2"
        row["loops_changed"] = row["change_group"] == "Changes the loops"
        run = (row["repo"], row["skill"], row["model"])
        rows_by_run.setdefault(run, []).append(row)

    multi = 0                                           # repairs that change several functions
    for row in rows:
        if row["functions_changed"] > 1:
            multi = multi + 1

    summary = {}
    summary["all"] = outcome(rows)                      # verdicts of every measured repair
    summary["measured"] = len(rows)
    summary["repairs_changing_more_than_one_function"] = multi
    middle = median([row["lines_changed"] for row in rows])
    summary["median_lines_changed"] = int(middle) if middle == int(middle) else middle
    summary["bootstrap"] = "resampling the 18 runs, 10,000 times, seed 7 (bootstrap.py)"
    # Estimates on all repairs: 95% intervals
    summary["pct_confirmed_all"] = interval(rows_by_run, pct_confirmed, 95.0)
    summary["median_saving_all"] = interval(rows_by_run, median_confirmed_saving, 95.0)
    # The three comparisons: Bonferroni-adjusted intervals
    summary["comparisons"] = COMPARISONS
    summary["median_saving_unflagged_minus_flagged"] = interval(
        rows_by_run, difference(median_confirmed_saving, "rule_flagged_unit", False, True),
        COMPARISON_LEVEL)
    summary["pct_confirmed_larger_minus_small"] = interval(
        rows_by_run, difference(pct_confirmed, "small", False, True), COMPARISON_LEVEL)
    summary["median_saving_loops_changed_minus_others"] = interval(
        rows_by_run, difference(median_confirmed_saving, "loops_changed", True, False),
        COMPARISON_LEVEL)
    write_json(summary, OUT / "repairs_summary.json")
    print("wrote", OUT / "repairs_*")


if __name__ == "__main__":
    main()
