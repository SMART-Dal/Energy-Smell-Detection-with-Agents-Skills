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

import importlib
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path

from . import __path__ as _ANALYSIS_PATH, __name__ as _ANALYSIS_PACKAGE
from .callgraph import CallSite, calls_made_by, link
from .context import UnitContext, collect_imports
from .models import Evidence, Strength, UnitRef
from .units import iter_units, parse_file, unit_source

_INFRASTRUCTURE = {"engine", "callgraph", "context", "models", "units"}
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
    max_loop_depth: int = 0
    """Loop nesting written inside this unit itself."""
    uses_arrays: bool = False

    calls: list[tuple[str, int, int]] = field(default_factory=list)
    """Raw (name, line, loop depth) call sites, before resolution."""
    called_from: list[CallSite] = field(default_factory=list)
    fan_in: int = 0
    """Distinct units in this file that call this one."""
    fan_out: set = field(default_factory=set)
    """Distinct units in this file that this one calls."""
    reached_at_depth: int = 0
    """Deepest loop nesting this unit runs under, counting its callers.

    Equal to `max_loop_depth` for a unit nothing calls; larger for a helper
    invoked from inside someone else's nested loop.  See callgraph.py.
    """

    @property
    def suggested_root_causes(self) -> set[str]:
        """Union of every root cause any evidence points at."""
        return {rc for item in self.evidence for rc in item.suggests}

    @property
    def suggested_categories(self) -> set[str]:
        return {rc.split(".")[0] for rc in self.suggested_root_causes}

    def evidence_of(self, *strengths: Strength) -> list[Evidence]:
        return [item for item in self.evidence if item.strength in strengths]

    @property
    def evidence_weight(self) -> int:
        """Evidence weighted by strength rather than counted.

        Counting raw hits ranks by whichever analyzers are chattiest: on real
        code the two most context-dependent rules produced 40% of all evidence,
        so an unweighted count would put ordinary API wrappers above genuine
        quadratic loops.
        """
        return (
            4 * len(self.evidence_of(Strength.DEFINITE))
            + 2 * len(self.evidence_of(Strength.LIKELY))
            + len(self.evidence_of(Strength.CONTEXTUAL))
        )

    @property
    def priority(self) -> tuple[int, int, int, int]:
        """Ranking key: how hot the unit is, then how strong the evidence is.

        Hotness leads because energy is spent per execution, so the same smell
        is worth 10 000 times more inside a doubly-nested loop than in
        straight-line code.  Two things make a unit hot, and both count:

            reached_at_depth  loop nesting including the callers that reach it,
                              so a helper called from someone else's nested loop
                              is not ranked as though it ran once
            fan_in            how many places call it, which catches the hot
                              utility that sits in no loop at all

        This is still a static guess.  It cannot see how many times a loop
        actually trips, or that a branch is never taken in practice, and it
        knows nothing about calls from other files.  It orders a reading list;
        it does not decide anything.
        """
        return (
            self.reached_at_depth,
            min(self.fan_in, 5),
            self.evidence_weight,
            len(self.suggested_root_causes),
        )


def _measure_unit(node, source: str, imports: dict):
    """Structural facts about one unit: loop depth, array use, call sites.

    Computed here rather than by an analyzer, because they are what ranks the
    reading list and must be available whether or not any analyzer is.
    """
    return UnitContext(node=node, source=source, imports=imports)


def _families() -> list:
    """Every analyzer family present in this package, in a stable order."""
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


def analyse_file(path: Path) -> list[UnitFindings]:
    """Run every available analyzer over one file, returning findings per unit."""
    tree = parse_file(path)
    if tree is None:
        return []

    source = path.read_text(encoding="utf-8", errors="replace")
    imports = collect_imports(tree)
    units = iter_units(path, tree)

    # A unit is where a repair gets scoped and measured. It is not a claim that
    # waste lives inside one function: waste that lives in the arrangement of
    # several units reaches the reader as a set of linked units, via the call
    # graph below, and recognising it from there is a reading job.
    findings: dict[str, UnitFindings] = {}
    for unit, node in units:
        if unit.kind == "class":
            continue
        contained = _measure_unit(node, source, imports)
        findings[unit.qualname] = UnitFindings(
            unit=unit,
            source=unit_source(source, unit),
            max_loop_depth=contained.max_loop_depth,
            uses_arrays=contained.uses_arrays,
            calls=calls_made_by(node, contained),
            reached_at_depth=contained.max_loop_depth,
        )

    for family in _families():
        try:
            produced = family.collect(path, units, source, imports)
        except Exception:  # noqa: BLE001 -- one family must not abort a scan
            continue
        for item in produced:
            if item.unit.qualname in findings:
                findings[item.unit.qualname].evidence.append(item)

    # Call edges are resolved after every unit in the file exists, since a
    # function is routinely called above its own definition.  This runs even
    # when no analyzer produced a single piece of evidence: it is structure,
    # not a smell rule, and it is what ranks the reading list.
    resolved = list(findings.values())
    link(resolved)
    return resolved


def analyse_path(root: Path, *, only_with_evidence: bool = True) -> list[UnitFindings]:
    """Analyse a file or a whole directory tree, ranked by priority.

    With `only_with_evidence`, units nothing flagged are dropped.  Pass it
    False to get the ranked reading list -- every unit, ordered by how hot it
    looks -- which is what you want before any analyzer has spoken.
    """
    results: list[UnitFindings] = []
    for path in python_files(root):
        results.extend(analyse_file(path))

    if only_with_evidence:
        results = [f for f in results if f.evidence]
    results.sort(key=lambda f: f.priority, reverse=True)
    return results


def python_files(root: Path) -> list[Path]:
    """Every .py file the scan should consider, in a stable order."""
    return [root] if root.is_file() else sorted(_walk(root))


def _walk(root: Path):
    """Yield every .py file under `root`, skipping vendored and build output."""
    for path in root.rglob("*.py"):
        if not any(part in SKIP_DIRECTORIES for part in path.parts):
            yield path
