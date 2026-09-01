"""Who calls whom, and from inside how many loops.

A unit's own loop nesting is a bad measure of how hot it is, and this module
exists because of exactly one counter-example:

    def distance(a, b):          # loop depth 0 -- looks cold
        return sum(abs(x - y) for x, y in zip(a, b))

    def cluster(points):
        for p in points:         # depth 1
            for q in points:     # depth 2
                d = distance(p, q)   <- `distance` runs len(points)**2 times

Ranking by a unit's own depth puts `cluster` first and `distance` nowhere, when
`distance` is where the energy goes.  So each unit also carries the deepest
loop nesting it is *reached* through, and how many distinct places call it.

Resolution is repo-wide, and `repo.RepoIndex` does the reading: it follows
import statements, aliases and re-exports to the file a call actually lands
in, and parameter annotations to the class a method call is made on.  Where it
cannot read the answer it says so, and this module falls back to matching the
call's short name against definitions *in the same file only* -- never across
files, where a shared short name means nothing.

Measured against the call graph our own test suite really executes: file-local
matching alone found 0 of 63 cross-file calls; with the index it finds 47.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

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
    """Repo-wide qualified name of the unit being called."""
    line: int
    repeat_depth: int
    """Loops and comprehensions enclosing the call *within the caller*.

    0 if the call is not repeated.  Comprehensions count: `[g(x) for x in xs]`
    calls `g` once per element exactly as a `for` statement would."""


def calls_made_by(unit_node: ast.AST, context: UnitContext, *,
                  index=None, path: Path | None = None,
                  binds: dict | None = None,
                  enclosing_class: str | None = None) -> list[tuple]:
    """Every call this unit makes, as (name, line, repeat depth, resolved).

    `resolved` is the repo-wide qualname the index could read off the source,
    or None when it could not.  A None is not a failure to report: most calls
    in any file go to the standard library or to a package outside the scan,
    and claiming those would be worse than leaving them out.
    """
    receivers = {}
    if index is not None and path is not None:
        module = index.module_of.get(path)
        if module is not None:
            receivers = index.receivers(unit_node, module, binds or {})

    found = []
    for node in ast.walk(unit_node):
        if not isinstance(node, ast.Call):
            continue
        name = _called_name(node.func)
        if name is None:
            continue
        resolved = None
        if index is not None and path is not None:
            module = index.module_of.get(path)
            if module is not None:
                resolved = index.resolve(node.func, module, binds or {},
                                         receivers, enclosing_class)
        found.append((name, node.lineno, context.repeat_depth(node), resolved))
    return found


def _called_name(func: ast.AST) -> str | None:
    """The bare name of a call target: `f()` -> "f", `self.f()` -> "f"."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def link(findings: list, index=None) -> None:
    """Fill in `called_from`, `fan_in` and `reached_at_depth` across the scan.

    Mutates the findings in place, because every caller already holds the list
    and threading a second structure through the engine would buy nothing.
    """
    key_of = {}
    by_key = {}
    for finding in findings:
        key = (index.qualname_in(finding.unit.path, finding.unit.qualname)
               if index is not None else finding.unit.qualname)
        key_of[id(finding)] = key
        by_key.setdefault(key, finding)
    in_file = _index_by_name(findings)

    # Pass 1: turn each unit's calls into edges.  A call the index resolved is
    # used as-is; one it could not is matched by short name against this file
    # only, never across files, where a shared short name means nothing.
    for caller in findings:
        caller_key = key_of[id(caller)]
        for name, line, depth, resolved in caller.calls:
            targets = []
            if resolved is not None and resolved in by_key:
                targets = [by_key[resolved]]
            elif resolved is None:
                targets = [
                    other for other in in_file.get(name, ())
                    if other.unit.path == caller.unit.path
                ]
            for callee in targets:
                if callee is caller:
                    continue  # direct recursion: a real edge, but not a hotness signal
                callee.called_from.append(
                    CallSite(
                        caller=caller_key,
                        callee=key_of[id(callee)],
                        line=line,
                        repeat_depth=depth,
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
    #                 distance(p, q)  <- call site at repeat_depth 2
    #
    #     def distance(a, b):         own 1, entered 2 -> reached 3
    #
    # Depth is only carried along edges that do not close a cycle.  Two mutually
    # recursive functions have no fixpoint, and each round used to add the
    # cycle's own depth again: in pandas that made `EABackedBlock.where` the
    # deepest unit in the package at depth 9, all of it manufactured by going
    # round the loop four times.
    entered = {key_of[id(f)]: 0 for f in findings}
    acyclic = _without_cycles(findings, key_of)

    for _ in range(MAX_PROPAGATION_ROUNDS):
        changed = False
        for finding in findings:
            key = key_of[id(finding)]
            for site in finding.called_from:
                if (site.caller, key) not in acyclic:
                    continue
                depth = entered.get(site.caller, 0) + site.repeat_depth
                if depth > entered[key]:
                    entered[key] = depth
                    changed = True
        if not changed:
            break

    for finding in findings:
        key = key_of[id(finding)]
        finding.reached_at_depth = finding.max_repeat_depth + entered[key]
        finding.fan_in = len({site.caller for site in finding.called_from})
        for site in finding.called_from:
            caller = by_key.get(site.caller)
            if caller is not None:
                caller.fan_out.add(site.callee)


def _without_cycles(findings: list, key_of: dict) -> set:
    """Edges that do not take part in a cycle, so depth can be carried along them.

    An edge is dropped when its callee can reach its caller again.  That is the
    only edge set on which "how deep am I entered" has an answer at all: around
    a cycle the question has none, and answering it anyway inflates the depth
    by one lap per propagation round.
    """
    successors: dict[str, set[str]] = {}
    for finding in findings:
        key = key_of[id(finding)]
        for site in finding.called_from:
            successors.setdefault(site.caller, set()).add(key)

    def reaches(start: str, goal: str) -> bool:
        seen, stack = set(), [start]
        while stack:
            node = stack.pop()
            if node == goal:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(successors.get(node, ()))
        return False

    keep = set()
    for finding in findings:
        key = key_of[id(finding)]
        for site in finding.called_from:
            if not reaches(key, site.caller):
                keep.add((site.caller, key))
    return keep


def _index_by_name(findings: list) -> dict[str, list]:
    """Map every unit's short name to the units that could answer to it.

    Only consulted for calls the index could not read, and only ever matched
    within the calling file.  A file with `Parser.parse` and `Lexer.parse`
    gives two entries under "parse", and a call to `self.parse` matches both;
    keeping both is the conservative choice, since picking one at random would
    be silently wrong half the time.
    """
    index: dict[str, list] = {}
    for finding in findings:
        short = finding.unit.qualname.rsplit(".", 1)[-1]
        index.setdefault(short, []).append(finding)
    return index
