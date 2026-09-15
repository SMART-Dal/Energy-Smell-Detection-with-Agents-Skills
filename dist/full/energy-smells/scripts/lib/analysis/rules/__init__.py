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

import ast
import collections
from pathlib import Path

from ..context import (
    UnitContext,
    collect_module_aliases,
    collect_module_bindings,
    collect_overridden_methods,
)
from ..models import Evidence, UnitRef
from . import loops, memory, structure, waste

ALL_RULES = [*loops.RULES, *memory.RULES, *structure.RULES, *waste.RULES]

RULE_ERRORS: collections.Counter = collections.Counter()
"""How many units each analyzer crashed on, keyed by `(rule name, exception)`.

An analyzer that raises is caught below so one brittle rule cannot abort a
whole repo, and that is right -- but until this counter existed the catch was
also silent, and a rule crashing on a third of the units it saw was
indistinguishable in the output from a rule that looked and found nothing.
Those are opposite facts, and a precision or recall figure computed over a
scan that hid the difference is not a figure about the rule.

Counts accumulate for the life of the process.  `scan.py` prints them to
stderr when the run ends, so they land beside the report rather than in it.
"""

__all__ = ["ALL_RULES", "RULE_ERRORS", "collect", "loops", "memory",
           "structure", "waste"]


def collect(
    path: Path,
    units: list[tuple[UnitRef, object]],
    source: str,
    imports: dict,
    entry_depth: dict[str, int] | None = None,
) -> list[Evidence]:
    """Run every analyzer over every function-like unit in one file.

    Classes are skipped, because running the function analyzers over a class
    body would re-report each method's findings a second time under the class.

    The module-level facts are collected here rather than passed in, because
    they were previously not collected at all: this built the context with
    `imports` only, so `module_bindings` was empty in every real scan while the
    rule tests supplied it. Any rule reading a module constant -- or asking
    whether a method is overridden -- was therefore tested under conditions the
    scan never reproduced, which is the exact gap `_harness.run` warns about
    from the other side. Re-parsing `source` is a few milliseconds per file and
    keeps the two paths honest.
    """
    tree = ast.parse(source)
    module_bindings = collect_module_bindings(tree)
    overridden = collect_overridden_methods(tree)
    aliases = collect_module_aliases(tree)

    found: list[Evidence] = []
    for unit, node in units:
        if unit.kind == "class":
            continue
        context = UnitContext(
            node=node, source=source, imports=imports,
            module_bindings=module_bindings, overridden_methods=overridden,
            module_aliases=aliases,
            entry_depth=(entry_depth or {}).get(unit.qualname, 0),
        )
        for rule in ALL_RULES:
            try:
                found.extend(rule(unit, context))
            except Exception as exc:  # noqa: BLE001
                # One brittle analyzer must not abort the scan of a whole repo.
                # Analyzers are heuristic by nature and meet strange code.
                #
                # Evidence already yielded before the raise is kept: `extend`
                # appends as it consumes, so a rule that fails on its fifth
                # yield still contributes its first four. Counting the failure
                # is what was missing, not recovering the partial result.
                RULE_ERRORS[(rule.__name__, type(exc).__name__)] += 1
                continue
    return found
