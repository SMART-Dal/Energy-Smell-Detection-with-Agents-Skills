"""Who calls whom, and from inside how many loops.

A unit's own loop nesting is a bad measure of how hot it is, and this module
exists because of exactly one counter-example:

    def distance(a, b):          # loop depth 0 -- looks cold
        return sum(abs(x - y) for x, y in zip(a, b))

    def cluster(points):
        for p in points:         # depth 1
            for q in points:     # depth 2
                d = distance(p, q)   <- `distance` runs len(points)**2 times

Ranking by `max_loop_depth` puts `cluster` first and `distance` nowhere, when
`distance` is where the energy goes.  So each unit also carries the deepest
loop nesting it is *reached* through, and how many distinct places call it.

Resolution is within one file only.  Following a call across a module boundary
means resolving imports, aliases and re-exports, and getting that wrong invents
call edges that do not exist -- worse than admitting the graph stops at the file
edge.  The agent is told to follow calls across files itself, which it can do
by reading, and this module does not pretend to have done it.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from .context import UnitContext

MAX_PROPAGATION_ROUNDS = 4
"""How far depth is carried along a call chain (a -> b -> c -> d).

Bounded rather than run to a fixpoint because recursive and mutually recursive
functions have no fixpoint, and because a unit four calls below a nested loop
is already too indirect for the number to mean much.
"""


@dataclass(frozen=True)
class CallSite:
    """One call, and how deeply nested it is inside its caller."""

    caller: str
    """Qualified name of the unit containing the call."""
    callee: str
    """Qualified name of the unit being called, resolved within this file."""
    line: int
    loop_depth: int
    """Loops enclosing the call *within the caller*: 0 if it is not in a loop."""


def calls_made_by(unit_node: ast.AST, context: UnitContext) -> list[tuple[str, int, int]]:
    """Every call this unit makes, as (name, line, enclosing loop depth).

    The name is whatever appears in the source -- `helper` for a plain call,
    `helper` for `self.helper` too, since the attribute's own qualifier tells us
    nothing useful once we are matching against names defined in this file.
    """
    found = []
    for node in ast.walk(unit_node):
        if not isinstance(node, ast.Call):
            continue
        name = _called_name(node.func)
        if name is not None:
            found.append((name, node.lineno, context.loop_depth(node)))
    return found


def _called_name(func: ast.AST) -> str | None:
    """The bare name of a call target: `f()` -> "f", `self.f()` -> "f"."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def link(findings: list) -> None:
    """Fill in `called_from`, `fan_in` and `reached_at_depth` across one file.

    Mutates the findings in place, because every caller already holds the list
    and threading a second structure through the engine would buy nothing.
    """
    by_name = _index_by_name(findings)

    # Pass 1: turn each unit's raw calls into edges, keeping only the ones that
    # land on a unit defined in this same file.
    for caller in findings:
        for name, line, depth in caller.calls:
            for callee in by_name.get(name, ()):
                if callee is caller:
                    continue  # direct recursion: a real edge, but not a hotness signal
                callee.called_from.append(
                    CallSite(
                        caller=caller.unit.qualname,
                        callee=callee.unit.qualname,
                        line=line,
                        loop_depth=depth,
                    )
                )

    # Pass 2: carry depth down the call chain.
    #
    # `entered` is how deep a unit is *before it runs a line of its own* -- the
    # loops its callers were already inside. It must exclude the caller's own
    # nesting, or a helper called from a doubly-nested loop would be credited
    # with those two loops twice: once as the caller's depth, once as the depth
    # of the call site, which is measured within that same caller.
    #
    #     def cluster(points):        own 2, entered 0
    #         for p in points:
    #             for q in points:
    #                 distance(p, q)  <- call site at loop_depth 2
    #
    #     def distance(a, b):         own 1, entered 2 -> reached 3
    entered = {f.unit.qualname: 0 for f in findings}
    by_qualname = {f.unit.qualname: f for f in findings}

    for _ in range(MAX_PROPAGATION_ROUNDS):
        changed = False
        for finding in findings:
            for site in finding.called_from:
                depth = entered.get(site.caller, 0) + site.loop_depth
                if depth > entered[finding.unit.qualname]:
                    entered[finding.unit.qualname] = depth
                    changed = True
        if not changed:
            break

    for finding in findings:
        finding.reached_at_depth = finding.max_loop_depth + entered[finding.unit.qualname]
        finding.fan_in = len({site.caller for site in finding.called_from})
        for site in finding.called_from:
            caller = by_qualname.get(site.caller)
            if caller is not None:
                caller.fan_out.add(site.callee)


def _index_by_name(findings: list) -> dict[str, list]:
    """Map every unit's short name to the units that could answer to it.

    A file with `Parser.parse` and `Lexer.parse` gives two entries under
    "parse", and a call to `self.parse` matches both.  Keeping both is the
    conservative choice: over-linking inflates a depth estimate, while picking
    one at random would be silently wrong half the time.
    """
    index: dict[str, list] = {}
    for finding in findings:
        short = finding.unit.qualname.rsplit(".", 1)[-1]
        index.setdefault(short, []).append(finding)
    return index
