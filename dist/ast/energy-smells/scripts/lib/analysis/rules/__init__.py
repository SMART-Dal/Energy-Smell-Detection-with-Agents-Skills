"""All tree-walking analyzers, gathered into one list.

An analyzer is just a function:

    def rule(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]

No base class, no registration decorator, no plugin discovery.  To add one,
write the function in the appropriate module and append it to that module's
`RULES` list.

This package is also an *analyzer family* in the sense `engine.py` uses: it
exposes `collect()`, which is how the engine reaches it without naming it.
"""

from __future__ import annotations

from pathlib import Path

from ..context import UnitContext
from ..models import Evidence, UnitRef
from . import loops, memory, structure, waste

ALL_RULES = [*loops.RULES, *memory.RULES, *structure.RULES, *waste.RULES]

__all__ = ["ALL_RULES", "collect", "loops", "memory", "structure", "waste"]


def collect(
    path: Path,
    units: list[tuple[UnitRef, object]],
    source: str,
    imports: dict,
) -> list[Evidence]:
    """Run every analyzer over every function-like unit in one file.

    Classes are skipped, because running the function analyzers over a class
    body would re-report each method's findings a second time under the class.
    """
    found: list[Evidence] = []
    for unit, node in units:
        if unit.kind == "class":
            continue
        context = UnitContext(node=node, source=source, imports=imports)
        for rule in ALL_RULES:
            try:
                found.extend(rule(unit, context))
            except Exception:  # noqa: BLE001
                # One brittle analyzer must not abort the scan of a whole repo.
                # Analyzers are heuristic by nature and meet strange code.
                continue
    return found
