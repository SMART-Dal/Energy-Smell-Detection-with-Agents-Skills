"""Ruff adapter: borrow the checks someone else already got right.

Ruff implements a number of the patterns in this taxonomy with high precision
and zero cost, so there is no reason to reimplement them.  It is a supplement,
not a foundation: measured over 300 real samples, energy-relevant Ruff rules
fired on only 21% of files.

Only rules that map onto a specific root cause are enabled.  Ruff's default
selection is dominated by unused imports and style, which would drown the
signal in noise.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .models import Evidence, UnitRef

# Ruff rule code -> (root cause IDs it indicates, short explanation).
# Every entry here was checked against the rule's actual semantics; a rule that
# only *sometimes* implies its root cause is left out rather than guessed at.
RULE_MAP: dict[str, tuple[tuple[str, ...], str]] = {
    "B006": (("C6.S7",), "mutable default argument"),
    "B019": (("C8.S1",), "cache decorator on a method leaks instances"),
    "B020": (("C3.S7",), "loop variable overwrites the iterable"),
    "B909": (("C3.S7",), "collection mutated while being iterated"),
    "C400": (("C6.S3",), "generator passed to list() unnecessarily"),
    "C401": (("C6.S3",), "generator passed to set() unnecessarily"),
    "C402": (("C6.S3",), "generator passed to dict() unnecessarily"),
    "C403": (("C5.S4",), "list comprehension converted to a set"),
    "C404": (("C5.S4",), "list comprehension converted to a dict"),
    "C405": (("C5.S4",), "literal converted to a set"),
    "C406": (("C5.S4",), "literal converted to a dict"),
    "C408": (("C6.S1",), "collection call where a literal would do"),
    "C409": (("C5.S4",), "literal rebuilt inside tuple()"),
    "C410": (("C5.S4",), "literal rebuilt inside list()"),
    "C411": (("C5.S4",), "redundant list() around a comprehension"),
    "C413": (("C5.S4",), "redundant call around sorted()"),
    "C414": (("C5.S4",), "redundant double cast"),
    "C416": (("C5.S4",), "comprehension that only copies"),
    "C417": (("C10.S2",), "map() where a comprehension is faster"),
    "C419": (("C6.S3",), "comprehension materialised inside any()/all()"),
    "F841": (("C1.S1",), "local assigned but never read"),
    "PERF101": (("C5.S4",), "unnecessary list() cast before iteration"),
    "PERF102": (("C3.S1",), "iterating dict items when only keys or values are used"),
    "PERF203": (("C4.S6",), "try/except inside a loop body"),
    "PERF401": (("C3.S1", "C10.S3"), "append loop that could be a comprehension"),
    "PERF402": (("C10.S3",), "manual copy loop where list() or slicing would do"),
    "PERF403": (("C3.S1",), "manual dict build that could be a comprehension"),
    "PLR1730": (("C10.S1",), "if/assign that reimplements min() or max()"),
    "PLW2901": (("C1.S2",), "loop variable overwritten before it is read"),
    "RUF005": (("C6.S1",), "list concatenation allocating a new list"),
    "RUF015": (("C6.S3",), "whole iterable materialised to take the first element"),
    "RUF017": (("C7.S1",), "quadratic list summation"),
    "SIM110": (("C10.S1",), "loop that reimplements any() or all()"),
    "SIM115": (("C6.S6",), "file opened without a context manager"),
    "SIM118": (("C10.S2",), "`in dict.keys()` instead of `in dict`"),
    "SIM401": (("C10.S2",), "if/else block instead of dict.get()"),
}


def ruff_executable() -> str | None:
    """Find Ruff on PATH, or beside the interpreter that is running us.

    The second case is the common one: a project installs ruff into its
    virtualenv, then invokes `.venv/bin/python scan.py` without activating it,
    so PATH never sees the binary.  Missing it there would silently drop an
    evidence source without anyone noticing.
    """
    found = shutil.which("ruff")
    if found:
        return found
    beside = Path(sys.executable).parent / "ruff"
    return str(beside) if beside.exists() else None


def ruff_available() -> bool:
    return ruff_executable() is not None


def run_ruff(path: Path) -> list[dict]:
    """Run Ruff over one file with only our mapped rules enabled."""
    executable = ruff_executable()
    if executable is None:
        return []
    completed = subprocess.run(
        [executable, "check", "--isolated", "--no-cache", "--output-format", "json",
         "--select", ",".join(sorted(RULE_MAP)), str(path)],
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(completed.stdout or "[]")
    except ValueError:
        return []


def unavailable_reason() -> str | None:
    """Why this family cannot run, or None when it can. See analysis/__init__."""
    if ruff_available():
        return None
    return "ruff is not on PATH or beside this interpreter (`pip install ruff`)"


def collect(path: Path, units, source: str, imports: dict) -> list[Evidence]:
    """The analyzer-family entry point. See `analysis/__init__.py`."""
    return evidence_from_ruff(path, [unit for unit, _ in units], source)


def evidence_from_ruff(path: Path, units: list[UnitRef],
                       source: str | None = None) -> list[Evidence]:
    """Turn Ruff findings into Evidence, attributed to the unit they fall in."""
    caught = _exception_binding_lines(source)
    findings = []
    for violation in run_ruff(path):
        code = violation.get("code")
        if code not in RULE_MAP:
            continue
        line = violation.get("location", {}).get("row", 0)
        # An unused `except ... as e` is dead *naming*, not dead work. C1.S1 is
        # measured on dead code that computes something -- a loop over 300,000
        # records -- so routing an unbound exception there ranked "delete `as e`"
        # as the most valuable repair in the file. Nothing is computed to
        # produce `e`, and deleting the binding saves nothing at all.
        if code == "F841" and line in caught:
            continue
        unit = _owning_unit(units, line)
        if unit is None:
            continue
        suggests, explanation = RULE_MAP[code]
        findings.append(
            Evidence(
                kind=f"ruff_{code}",
                unit=unit,
                lineno=line,
                suggests=suggests,
                message=f"{explanation} (ruff {code}: {violation.get('message', '')})",
                detail={"code": code},
                source="ruff",
            )
        )
    return findings


def _exception_binding_lines(source: str | None) -> set[int]:
    """Lines whose only binding is an `except ... as name` handler."""
    if not source:
        return set()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    return {
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.name
    }


def _owning_unit(units: list[UnitRef], line: int) -> UnitRef | None:
    """The innermost unit containing a line, or None if it is module-level."""
    containing = [u for u in units if u.lineno <= line <= u.end_lineno]
    return min(containing, key=lambda u: u.end_lineno - u.lineno) if containing else None
