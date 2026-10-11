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
import functools
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .models import Evidence, UnitRef

# Ruff rule code -> (root cause IDs it indicates, short explanation).
# Every entry here was checked against the rule's actual semantics; a rule that
# only *sometimes* implies its root cause is left out rather than guessed at.
#
# Three were removed on that test rather than added to it:
#
#   B020    `for x in x:` shadows a name. C3.S7 is a collection edited while it
#           is walked, which B020 neither checks nor implies.
#   PLW2901 a loop variable reassigned in the body. The repair is a rename, and
#           C1.S2 is measured on a *removable* store, of which there is none.
#   PERF203 any try/except inside a loop. C4.S6's own card says the cost is the
#           raise rate and not the syntax, and ruff stops emitting this above
#           target-version py310 because 3.11 made entering a `try` free -- so
#           it was firing on the strength of a default we never set. The same
#           shape still reaches the report through `try_except_in_loop`, which
#           says what it has seen rather than asserting the premise.
#   B909    collection mutated while iterated -- the right check for C3.S7, and
#           preview-gated in ruff 0.16, where selecting it without `--preview`
#           warns on stderr and exits 0. So it had never fired. `--preview` is
#           not the fix: it also broadens stable rules (11 more C419 hits on the
#           evaluation corpus) and makes the output move with ruff's unreleased
#           behaviour, which a reported rule count cannot rest on.
#           `mutation_during_iteration` carries C3.S7 on its own.
RULE_MAP: dict[str, tuple[tuple[str, ...], str]] = {
    "B006": (("C6.S7",), "mutable default argument"),
    "B019": (("C8.S1",), "cache decorator on a method leaks instances"),
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
    "PERF401": (("C3.S1", "C10.S3"), "append loop that could be a comprehension"),
    "PERF402": (("C10.S3",), "manual copy loop where list() or slicing would do"),
    "PERF403": (("C3.S1",), "manual dict build that could be a comprehension"),
    "PLR1730": (("C10.S1",), "if/assign that reimplements min() or max()"),
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


def _ruff_command(executable: str) -> list[str]:
    return [executable, "check", "--isolated", "--no-cache",
            "--output-format", "json", "--select", ",".join(sorted(RULE_MAP))]


_BATCHED: dict[Path, list[dict]] = {}
"""Violations from one Ruff run over the whole scan, by resolved file path."""

BATCH_SIZE = 400
"""Files per Ruff invocation, to stay well inside the command-line limit."""


def prepare(paths: list[Path]) -> None:
    """Run Ruff once over every file the scan will visit, ahead of `collect`.

    One process per file was most of the time this family took -- startup, not
    checking. A batch that fails leaves nothing behind, and `run_ruff` then runs
    each file on its own exactly as before, so an error still surfaces per file
    rather than vanishing into a clean report.
    """
    _BATCHED.clear()
    executable = ruff_executable()
    if executable is None or unavailable_reason() is not None:
        return
    found: dict[Path, list[dict]] = {path.resolve(): [] for path in paths}
    for start in range(0, len(paths), BATCH_SIZE):
        chunk = [str(path) for path in paths[start:start + BATCH_SIZE]]
        try:
            completed = subprocess.run([*_ruff_command(executable), *chunk],
                                       capture_output=True, text=True, timeout=600,
                                       check=False)
            if completed.returncode not in (0, 1):
                return
            violations = json.loads(completed.stdout or "[]")
        except (OSError, subprocess.SubprocessError, ValueError):
            return
        for violation in violations:
            filename = violation.get("filename")
            if filename:
                found.setdefault(Path(filename).resolve(), []).append(violation)
    _BATCHED.update(found)


def run_ruff(path: Path) -> list[dict]:
    """Run Ruff over one file with only our mapped rules enabled.

    Ruff exits 0 with no findings, 1 with findings, and 2 on an error -- an
    unknown rule selector, a config it cannot read -- where everything goes to
    stderr and stdout is empty.  Parsing stdout alone read that as a clean file,
    so a selection one ruff version does not recognise turned this whole
    evidence family off across an entire corpus while the report went on saying
    it had run.  Raising is the point: the caller may drop the family, but it
    cannot mistake it for silence.
    """
    batched = _BATCHED.get(path.resolve())
    if batched is not None:
        return batched
    executable = ruff_executable()
    if executable is None:
        return []
    completed = subprocess.run(
        [*_ruff_command(executable), str(path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode not in (0, 1):
        raise RuntimeError(
            f"ruff exited {completed.returncode}: {completed.stderr.strip()[:400]}"
        )
    try:
        return json.loads(completed.stdout or "[]")
    except ValueError:
        return []


@functools.lru_cache(maxsize=1)
def unavailable_reason() -> str | None:
    """Why this family cannot run, or None when it can. See analysis/__init__.

    Being on PATH is not enough to be usable: the rule selection has to be one
    this ruff understands, and a selector it does not is a hard error that stops
    every file rather than one.  So the selection is tried once, on nothing, and
    the failure is reported here -- where a reader sees it -- instead of per file
    inside a handler that drops the family without a word.
    """
    executable = ruff_executable()
    if executable is None:
        return "ruff is not on PATH or beside this interpreter (`pip install ruff`)"
    try:
        completed = subprocess.run(
            [*_ruff_command(executable), "--stdin-filename", "check.py", "-"],
            input="", capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return f"ruff could not be run: {error}"
    if completed.returncode not in (0, 1):
        return (f"ruff rejects this rule selection "
                f"(exit {completed.returncode}): {completed.stderr.strip()[:200]}")
    return None


def collect(path: Path, units, source: str, imports: dict) -> list[Evidence]:
    """The analyzer-family entry point. See `analysis/__init__.py`."""
    return evidence_from_ruff(path, [unit for unit, _ in units], source)


def evidence_from_ruff(path: Path, units: list[UnitRef],
                       source: str | None = None) -> list[Evidence]:
    """Turn Ruff findings into Evidence, attributed to the unit they fall in."""
    caught = _exception_binding_lines(source)
    impure = _impure_binding_lines(source)
    findings = []
    for violation in run_ruff(path):
        code = violation.get("code")
        if code not in RULE_MAP:
            continue
        line = violation.get("location", {}).get("row", 0)
        # A dead *name* is not dead *work*, and C1.S1 is measured on work: a
        # loop over 300,000 records, at 96%. Two shapes bind a name nothing
        # reads while the thing that produced it still has to run --
        #
        #     except Exception as e:          nothing is computed to make `e`
        #     response = requests.post(url)   the request is sent regardless
        #
        # -- so the repair removes a store and nothing else. Reporting them
        # made "delete `as e`" the most valuable repair in a file. The lint is
        # real; the energy claim is not, so neither is reported here.
        if code == "F841" and (line in caught or line in impure):
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
    """Lines whose only binding is an `except ... as name` handler.

    The whole header, not just the `except` keyword's line.  Ruff reports the
    unused binding where the name is written, and a handler whose exception
    tuple wraps puts that a line or two lower than `node.lineno`.
    """
    if not source:
        return set()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.name:
            last = node.body[0].lineno if node.body else node.lineno + 1
            lines.update(range(node.lineno, last))
    return lines


PURE_ENOUGH_TO_DELETE = frozenset({
    "len", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "sorted", "sum", "min", "max", "abs", "round", "range", "repr", "zip",
})
"""Calls whose only effect is the value they return, so deleting removes work."""


def _impure_binding_lines(source: str | None) -> set[int]:
    """Lines binding a dead name to something that has to run anyway.

    A call this cannot vouch for keeps happening once the name is gone, so the
    repair removes a store and nothing else.
    """
    if not source:
        return set()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()

    lines: set[int] = set()
    for node in ast.walk(tree):
        value = getattr(node, "value", None)
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)) or value is None:
            continue
        for call in [n for n in ast.walk(value) if isinstance(n, ast.Call)]:
            func = call.func
            named = func.id if isinstance(func, ast.Name) else None
            if named not in PURE_ENOUGH_TO_DELETE:
                lines.add(node.lineno)
                break
    return lines


def _owning_unit(units: list[UnitRef], line: int) -> UnitRef | None:
    """The innermost unit containing a line, or None if it is module-level.

    Measured from `first_lineno`, so a finding reported on a decorator belongs
    to the thing decorated.  Ruff puts B019 on the `@lru_cache` line, which sits
    above the `def` and inside the class body: attributed to the class, and
    class-attributed evidence is dropped, so the rule reached no report at all.
    """
    containing = [u for u in units if u.first_lineno <= line <= u.end_lineno]
    if not containing:
        return None
    return min(containing, key=lambda u: u.end_lineno - u.first_lineno)
