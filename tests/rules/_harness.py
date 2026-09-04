"""Run one analyzer over one file of test cases and compare against expectations.

Each rule gets a directory holding two files:

    tests/rules/<rule_name>/test_cases.py   the code under test
    tests/rules/<rule_name>/test_main.py    what the rule should say about it

`test_cases.py` is ordinary Python -- a handful of small functions or classes,
some the rule is supposed to flag and some it is not. `test_main.py` names the
ones it should flag and how many times, and everything it does not name must
come back with nothing.

The count matters as much as the set. A rule that reports the right function
three times has a bug (it happened: four rules walked every enclosing loop, so a
statement inside three nested loops was reported once per level), and a set
comparison would not have noticed.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from lib.analysis.context import (  # noqa: E402
    UnitContext,
    collect_imports,
    collect_module_aliases,
    collect_module_bindings,
    collect_overridden_methods,
)
from lib.analysis.rules import ALL_RULES  # noqa: E402
from lib.analysis.units import iter_units  # noqa: E402


class RuleTestFailure(AssertionError):
    """A rule said something other than what its test file expects."""


def rule_named(name: str):
    """Look a rule up by name, so a test file need not know which module it is in."""
    for rule in ALL_RULES:
        if rule.__name__ == name:
            return rule
    raise LookupError(f"no analyzer named {name!r}")


def run(rule, path: Path) -> list:
    """Every piece of evidence `rule` produces for `path`, in source order.

    The context is assembled exactly as `engine.analyse_file` assembles it. A
    harness that builds a different context tests a rule the scan never runs,
    and that gap hid a false negative once: module-level constants were absent
    here, so no test could notice that a rule could not see them.
    """
    source = path.read_text()
    tree = ast.parse(source)
    imports = collect_imports(tree)
    module_bindings = collect_module_bindings(tree)
    overridden = collect_overridden_methods(tree)
    aliases = collect_module_aliases(tree)
    found = []
    for unit, node in iter_units(path, tree):
        if unit.kind == "class":
            continue
        context = UnitContext(
            node=node, source=source, imports=imports,
            module_bindings=module_bindings,
            overridden_methods=overridden,
            module_aliases=aliases,
        )
        found.extend(rule(unit, context))
    return sorted(found, key=lambda e: e.lineno)


def hits(rule, path: Path) -> dict[str, int]:
    """Unit qualname -> how many times the rule flagged it."""
    counts: dict[str, int] = {}
    for item in run(rule, path):
        counts[item.unit.qualname] = counts.get(item.unit.qualname, 0) + 1
    return counts


def check(rule_name: str, cases: Path, expected: dict[str, int]) -> None:
    """Compare what the rule said against what the test file expects.

    Reports every disagreement at once rather than the first, because a rule
    that has been tightened usually moves several cases together and seeing
    them one at a time is slow going.
    """
    rule = rule_named(rule_name)
    actual = hits(rule, cases)
    problems = []

    for unit in sorted(set(expected) | set(actual)):
        want, got = expected.get(unit, 0), actual.get(unit, 0)
        if want == got:
            continue
        if want == 0:
            problems.append(f"  false positive: {unit} flagged {got}x, should be quiet")
        elif got == 0:
            problems.append(f"  false negative: {unit} not flagged, expected {want}x")
        else:
            problems.append(f"  wrong count:    {unit} flagged {got}x, expected {want}x")

    if problems:
        lines = [f"{rule_name} disagrees with {cases.parent.name}/{cases.name}:"]
        lines += problems
        lines.append("")
        lines.append("  what it actually reported:")
        for item in run(rule, cases):
            lines.append(f"    line {item.lineno:>3}  {item.unit.qualname}: {item.message}")
        raise RuleTestFailure("\n".join(lines))


def units_in(cases: Path) -> list[str]:
    """Every function-like unit in a cases file, for the coverage check."""
    tree = ast.parse(cases.read_text())
    return [u.qualname for u, _ in iter_units(cases, tree) if u.kind != "class"]
