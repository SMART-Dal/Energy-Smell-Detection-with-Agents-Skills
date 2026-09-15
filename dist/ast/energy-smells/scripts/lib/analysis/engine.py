"""Runs the analyzers over a file or a repository and ranks what they find.

This is the whole static layer's entry point.  It produces `Evidence`, never
claims: deciding whether a fact is actually a smell needs context an analyzer
cannot see, and is the reading agent's job.

Analyzers are discovered, not configured.  Every module in this package that
defines `collect()` is an analyzer family and gets run; nothing here holds a
list of which families should exist, so an installation with fewer of them
behaves exactly like one that never had more.  There is no flag and no config
file: a scan reports what this installation can see, and `available_analyzers()`
says what that was.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path

from . import __path__ as _ANALYSIS_PATH, __name__ as _ANALYSIS_PACKAGE
from .callgraph import CallSite, calls_made_by, link
from .repo import RepoIndex
from .context import (
    UnitContext,
    collect_imports,
    collect_module_aliases,
    collect_module_bindings,
    collect_overridden_methods,
)
from .models import Evidence, UnitRef
from .units import iter_units, parse_file, unit_source

_INFRASTRUCTURE = {"engine", "callgraph", "context", "models", "repo", "units"}
"""Modules in this package that are plumbing rather than analyzer families.

Named rather than probed, because a module that happens to grow a function
called `collect` should not silently become an analyzer.
"""

SKIP_DIRECTORIES = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "build", "dist",
    ".tox", ".mypy_cache", ".pytest_cache", "site-packages", ".eggs",
}


@dataclass
class UnitFindings:
    """Everything the static layer knows about one unit."""

    unit: UnitRef
    source: str
    evidence: list[Evidence] = field(default_factory=list)
    max_repeat_depth: int = 0
    """Repeat nesting written inside this unit itself.

    Comprehensions count: they repeat, so a line inside one runs as many times
    as the equivalent `for` would."""
    uses_arrays: bool = False

    calls: list[tuple] = field(default_factory=list)
    """(name, line, repeat depth, resolved qualname or None) call sites."""
    called_from: list[CallSite] = field(default_factory=list)
    fan_in: int = 0
    """Distinct units that call this one, anywhere in the scan."""
    fan_out: set = field(default_factory=set)
    """Distinct units this one calls, anywhere in the scan."""
    reached_at_depth: int = 0
    """Deepest repeat nesting this unit runs under, counting its callers.

    Equal to `max_repeat_depth` for a unit nothing calls; larger for a helper
    invoked from inside someone else's nested loop.  See callgraph.py.
    """

    @property
    def suggested_root_causes(self) -> set[str]:
        """Union of every root cause any evidence points at."""
        return {rc for item in self.evidence for rc in item.suggests}

    @property
    def suggested_categories(self) -> set[str]:
        return {rc.split(".")[0] for rc in self.suggested_root_causes}

    @property
    def distinct_signals(self) -> int:
        """How many different rules fired, not how many times they fired.

        Counting raw hits ranks by whichever analyzers are chattiest: on real
        code the two most context-dependent rules produced 40% of all evidence,
        so one repeated attribute lookup would outrank a quadratic loop. This is
        only a tiebreak -- what a finding is worth is measured, and lives in
        `signals.json`, which the engine deliberately does not read."""
        return len({item.kind for item in self.evidence})

    @property
    def priority(self) -> tuple[int, int, int, int]:
        """Ranking key: how hot the unit is, then how varied the evidence is.

        Hotness leads because energy is spent per execution, so the same smell
        is worth 10 000 times more inside a doubly-nested loop than in
        straight-line code.  Two things make a unit hot, and both count:

            reached_at_depth  loop nesting including the callers that reach it,
                              so a helper called from someone else's nested loop
                              is not ranked as though it ran once
            fan_in            how many places call it, which catches the hot
                              utility that sits in no loop at all

        This is still a static guess.  It cannot see how many times a loop
        actually trips, or that a branch is never taken in practice, and about
        four call sites in five it cannot name the callee at all.  It orders a
        reading list; it does not decide anything.
        """
        return (
            self.reached_at_depth,
            min(self.fan_in, 5),
            self.distinct_signals,
            len(self.suggested_root_causes),
        )


def _measure_unit(node, source: str, imports: dict, module_bindings: dict | None = None,
                  overridden_methods: frozenset[str] = frozenset(),
                  module_aliases: frozenset[str] = frozenset()):
    """Structural facts about one unit: loop depth, array use, call sites.

    Computed here rather than by an analyzer, because they are what ranks the
    reading list and must be available whether or not any analyzer is.
    """
    return UnitContext(
        node=node, source=source, imports=imports,
        module_bindings=module_bindings or {},
        overridden_methods=overridden_methods,
        module_aliases=module_aliases,
    )


@functools.lru_cache(maxsize=1)
def _families() -> list:
    """Every analyzer family present in this package, in a stable order.

    Cached: `analyse_file` asks once per file, and `pkgutil.iter_modules` re-stats
    the package directory every time it is asked.  What is installed does not
    change while a scan runs.
    """
    found = []
    for info in sorted(pkgutil.iter_modules(_ANALYSIS_PATH), key=lambda i: i.name):
        if info.name in _INFRASTRUCTURE or info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{_ANALYSIS_PACKAGE}.{info.name}")
        except ImportError:
            continue
        if callable(getattr(module, "collect", None)):
            found.append(module)
    return found


def available_analyzers() -> dict[str, str | None]:
    """Analyzer family -> why it cannot run, or None when it can.

    `scan.py` uses this to fail loudly rather than print an empty report, and
    to pass on whatever a family says about its own missing dependencies.
    """
    return {
        module.__name__.rsplit(".", 1)[-1]: (
            module.unavailable_reason()
            if callable(getattr(module, "unavailable_reason", None))
            else None
        )
        for module in _families()
    }


def analyse_file(path: Path, index: RepoIndex | None = None,
                 *, link_calls: bool = True, cross_unit: bool = False) -> list[UnitFindings]:
    """Run every available analyzer over one file, returning findings per unit.

    `index` is the repo-wide symbol table; without one, calls resolve inside
    this file only.  `link_calls` is False when a whole-tree scan will link
    every file together afterwards, which is the only way a cross-file edge can
    exist -- the callee's unit does not exist yet while its caller is analysed.

    `cross_unit` has little to offer here and is accepted for symmetry: on one
    file the only callers a unit can have are in that same file, so almost
    every unit's entry depth is zero whatever this says.
    """
    prepared = _structure_file(path, index)
    if prepared is None:
        return []
    _, units, source, imports, findings = prepared
    resolved = list(findings.values())
    if link_calls:
        link(resolved, index)
    _apply_rules(path, units, source, imports, findings, cross_unit=cross_unit)
    return resolved


def _structure_file(path: Path, index: RepoIndex | None):
    """Units and their structural facts for one file, with no analyzer run.

    Returned as `(path, units, source, imports, findings)` so a whole-tree scan
    can hold every file in this state, link them, and only then ask the rules
    anything.  Structure is what ranks the reading list and is computed whether
    or not any analyzer exists, so it was always separable; nothing needed it
    separated until a rule wanted to know about its callers.
    """
    # The index parsed every file to build the symbol table and kept the tree,
    # which is the reason it keeps it.  Parsing again is the single most
    # expensive thing a scan does per file.
    tree = (index.trees.get(path) if index is not None else None) or parse_file(path)
    if tree is None:
        return None

    source = path.read_text(encoding="utf-8", errors="replace")
    imports = collect_imports(tree)
    module_bindings = collect_module_bindings(tree)
    overridden = collect_overridden_methods(tree)
    aliases = collect_module_aliases(tree)
    units = iter_units(path, tree)

    # A unit is where a repair gets scoped and measured. It is not a claim that
    # waste lives inside one function: waste that lives in the arrangement of
    # several units reaches the reader as a set of linked units, via the call
    # graph below, and recognising it from there is a reading job.
    binds = index.bindings(path) if index is not None and path in index.trees else {}

    findings: dict[str, UnitFindings] = {}
    for unit, node in units:
        if unit.kind == "class":
            continue
        contained = _measure_unit(node, source, imports, module_bindings, overridden,
                                  aliases)
        # Only a method has an enclosing class. For a nested function this used
        # to hand `resolve` the *function* around it and ask it to look up
        # `outer.helper` in a table of classes, which cannot match anything.
        owner = unit.qualname.rsplit(".", 1)[0] if unit.kind == "method" else None
        findings[unit.qualname] = UnitFindings(
            unit=unit,
            source=unit_source(source, unit),
            max_repeat_depth=contained.max_repeat_depth,
            uses_arrays=contained.uses_arrays,
            calls=calls_made_by(node, contained, index=index, path=path,
                                binds=binds, enclosing_class=owner),
            reached_at_depth=contained.max_repeat_depth,
        )

    return path, units, source, imports, findings


def _entry_depth(finding: "UnitFindings") -> int:
    """How many loops a unit is already inside before it runs a line of its own.

    `link` computes this as `entered` and folds it away into
    `reached_at_depth`; the difference recovers it, so nothing in the call
    graph has to change to expose it.  Zero for a unit nothing calls, and for
    every unit when the scan is one file.
    """
    return max(0, finding.reached_at_depth - finding.max_repeat_depth)


def _accepts_entry_depth(family) -> bool:
    """Whether a family's `collect` takes the caller-context argument.

    Families are discovered, not declared, so a family that predates this
    argument -- or one a user drops in -- must keep working untouched.
    """
    try:
        return "entry_depth" in inspect.signature(family.collect).parameters
    except (TypeError, ValueError):  # pragma: no cover - builtins, C callables
        return False


def _apply_rules(path: Path, units, source: str, imports: dict,
                 findings: dict, *, cross_unit: bool) -> None:
    """Run every analyzer family and attach what it produces to its unit.

    Split out of `analyse_file` so it can run *after* `link`, which is the
    whole point: a rule that wants to know it sits inside a caller's loop
    cannot be told before the edge into it exists.  With `cross_unit` false
    nothing is passed and every rule sees exactly what it saw before.
    """
    depths = ({name: _entry_depth(f) for name, f in findings.items()}
              if cross_unit else None)
    for family in _families():
        extra = {"entry_depth": depths} if depths and _accepts_entry_depth(family) else {}
        try:
            produced = family.collect(path, units, source, imports, **extra)
        except Exception:  # noqa: BLE001 -- one family must not abort a scan
            continue
        for item in produced:
            if item.unit.qualname in findings:
                findings[item.unit.qualname].evidence.append(item)


def analyse_path(root: Path, *, only_with_evidence: bool = True,
                 cross_unit: bool = False) -> list[UnitFindings]:
    """Analyse a file or a whole directory tree, ranked by priority.

    With `only_with_evidence`, units nothing flagged are dropped.  Pass it
    False to get the ranked reading list -- every unit, ordered by how hot it
    looks -- which is what you want before any analyzer has spoken.
    """
    files = python_files(root)
    base = root if root.is_dir() else root.parent
    index = RepoIndex(base, files)

    # Structure first, rules second, with the link in between. A rule that asks
    # whether it runs inside a caller's loop has no answer until every file has
    # produced its units and the edges between them exist, so running the rules
    # file by file -- which is what this did -- could never answer it.
    prepared = [p for p in (_structure_file(path, index) for path in files) if p]
    results: list[UnitFindings] = [f for p in prepared for f in p[4].values()]

    # Linked once, over every unit in the tree: a call from `a.py` into `b.py`
    # can only become an edge after both files have produced their units.
    link(results, index)

    for path, units, source, imports, findings in prepared:
        _apply_rules(path, units, source, imports, findings, cross_unit=cross_unit)

    if only_with_evidence:
        results = [f for f in results if f.evidence]
    results.sort(key=lambda f: f.priority, reverse=True)
    return results


def python_files(root: Path) -> list[Path]:
    """Every .py file the scan should consider, in a stable order."""
    return [root] if root.is_file() else sorted(_walk(root))


def _walk(root: Path):
    """Yield every .py file under `root`, skipping vendored and build output.

    Matched against the path *below* the scan root, never the absolute path.
    A checkout that lives in `~/build/myproject` or under any directory sharing
    a name with this list matched on its own location and yielded nothing at
    all -- an empty scan, reported as a clean one.
    """
    for path in root.rglob("*.py"):
        if not any(part in SKIP_DIRECTORIES for part in path.relative_to(root).parts):
            yield path
