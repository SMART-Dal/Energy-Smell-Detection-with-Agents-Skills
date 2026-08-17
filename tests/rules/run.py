#!/usr/bin/env python3
"""Run every analyzer against the cases that say what it should and should not see.

    python tests/rules/run.py                 every rule
    python tests/rules/run.py missing_early_exit filter_after_transform
    python tests/rules/run.py --verbose        show every case, not just failures

This suite is not shipped. It exists so that a rule's precision is a fact we
can check rather than a hope, and so that tightening one rule cannot silently
loosen another.

## Layout

    tests/rules/<rule_name>/fires_<what>.py     the rule must fire
    tests/rules/<rule_name>/quiet_<what>.py     the rule must not fire

The prefix is the expectation. Inside a `fires_` case, put `# EXPECT` at the
end of every line the rule is supposed to flag; the reported lines then have to
match exactly, so a rule that fires on the right file for the wrong reason
still fails.

Each case file needs a docstring saying what it is testing. A `quiet_` case
without a stated reason is worthless -- the reason *is* the test.

## What a good set of cases looks like

Two or three `fires_` cases covering genuinely different shapes of the same
mistake, and at least three `quiet_` cases: code that looks like the pattern
and is correct, code where the pattern is present but the context makes it
right, and the boundary just outside what the rule claims. False positives are
what we are hunting -- a rule the reader learns to ignore is worse than no rule.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "src"))

from lib.analysis.context import UnitContext, collect_imports  # noqa: E402
from lib.analysis.rules import ALL_RULES  # noqa: E402
from lib.analysis.units import iter_units  # noqa: E402

MIN_FIRES = 2
MIN_QUIET = 3


@dataclass
class Failure:
    case: Path
    problem: str


def evidence_from(rule, path: Path) -> list:
    """Run one rule, and only that rule, over one file."""
    source = path.read_text()
    tree = ast.parse(source)
    imports = collect_imports(tree)
    found = []
    for unit, node in iter_units(path, tree):
        if unit.kind == "class":
            continue
        context = UnitContext(node=node, source=source, imports=imports)
        found.extend(rule(unit, context))
    return found


def expected_lines(path: Path) -> set[int]:
    """Line numbers marked `# EXPECT`, 1-based. Empty when none are marked."""
    return {
        number
        for number, text in enumerate(path.read_text().splitlines(), start=1)
        if text.rstrip().endswith("# EXPECT")
    }


def check_case(rule, path: Path) -> list[Failure]:
    """One case file against one rule."""
    problems = []
    if not ast.get_docstring(ast.parse(path.read_text())):
        problems.append(Failure(path, "no module docstring saying what this tests"))

    try:
        found = evidence_from(rule, path)
    except Exception as exc:  # noqa: BLE001
        return problems + [Failure(path, f"the rule raised {exc!r}")]

    lines = sorted(e.lineno for e in found)
    if path.name.startswith("quiet_"):
        if found:
            problems.append(
                Failure(path, f"fired on line(s) {lines} and should have stayed quiet")
            )
        return problems

    if not found:
        return problems + [Failure(path, "did not fire")]

    wanted = expected_lines(path)
    if wanted and set(lines) != wanted:
        problems.append(
            Failure(path, f"fired on {lines}, expected exactly {sorted(wanted)}")
        )
    # Duplicate evidence for one line is a bug in its own right: it inflates
    # the unit's ranking and makes the report look like several observations.
    if len(lines) != len(set(lines)):
        problems.append(Failure(path, f"reported a line more than once: {lines}"))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rules", nargs="*", help="rule names; default is all of them")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    by_name = {rule.__name__: rule for rule in ALL_RULES}
    wanted = args.rules or sorted(by_name)
    unknown = [name for name in wanted if name not in by_name]
    if unknown:
        parser.error(f"no such rule: {', '.join(unknown)}")

    failures: list[Failure] = []
    uncovered: list[str] = []
    checked = 0

    for name in wanted:
        directory = ROOT / name
        cases = sorted(directory.glob("*.py")) if directory.exists() else []
        fires = [c for c in cases if c.name.startswith("fires_")]
        quiet = [c for c in cases if c.name.startswith("quiet_")]
        strays = [c for c in cases if c not in fires and c not in quiet]

        if not cases:
            uncovered.append(name)
            continue
        if len(fires) < MIN_FIRES or len(quiet) < MIN_QUIET:
            failures.append(Failure(
                directory,
                f"{len(fires)} fires_ and {len(quiet)} quiet_ cases; "
                f"at least {MIN_FIRES} and {MIN_QUIET} are required",
            ))
        for stray in strays:
            failures.append(Failure(stray, "name must start with fires_ or quiet_"))

        for case in fires + quiet:
            checked += 1
            problems = check_case(by_name[name], case)
            failures.extend(problems)
            if args.verbose and not problems:
                print(f"  ok   {name}/{case.name}")

    for failure in failures:
        location = failure.case.relative_to(ROOT)
        print(f"FAIL {location}: {failure.problem}")
    if uncovered:
        print(f"\n{len(uncovered)} rule(s) with no cases at all:")
        for name in uncovered:
            print(f"  {name}")

    print(f"\n{checked} cases checked, {len(failures)} failure(s), "
          f"{len(uncovered)} rule(s) uncovered")
    return 1 if failures or uncovered else 0


if __name__ == "__main__":
    sys.exit(main())
