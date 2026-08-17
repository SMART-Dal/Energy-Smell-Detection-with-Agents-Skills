"""Analyzers for work done inside loops.

Loops are where energy smells concentrate, because anything wasteful in a loop
body is paid once per iteration.  These rules find *facts* ("this expression
does not change across iterations"), not verdicts -- deciding whether a fact is
actually a smell needs context that only the reader has.
"""

from __future__ import annotations

import ast
from typing import Iterator

from ..models import Evidence, Strength, UnitRef
from ..context import COMPREHENSION_NODES, LOOP_NODES, UnitContext

# Calls that build a fresh object; expensive to repeat inside a loop.
CONSTRUCTOR_NAMES = frozenset({"list", "dict", "set", "tuple", "frozenset", "bytearray"})

# Functions that compile or parse something reusable.
COMPILE_CALLS = {
    ("re", "compile"), ("re", "search"), ("re", "match"), ("re", "findall"),
    ("re", "sub"), ("re", "fullmatch"), ("re", "split"),
}


def _evidence(unit: UnitRef, kind: str, node: ast.AST, suggests: tuple[str, ...],
              message: str, strength: Strength = Strength.LIKELY, **detail) -> Evidence:
    return Evidence(
        kind=kind,
        unit=unit,
        lineno=getattr(node, "lineno", unit.lineno),
        suggests=suggests,
        message=message,
        strength=strength,
        detail=detail,
    )


def loop_invariant_expression(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Non-trivial pure expressions whose value cannot change across iterations.

    The highest-value analyzer in the suite.
    Only reports calls and subscripts -- hoisting a bare name or a literal buys
    nothing, and reporting those would bury the real findings in noise.
    """
    for loop in ctx.loops:
        rewritten = ctx.assigned_names(loop)
        reported: list[ast.AST] = []
        for node in ctx.per_iteration_nodes(loop):
            if not isinstance(node, (ast.Call, ast.Subscript)):
                continue
            if ctx.loops_around(node)[-1:] != (loop,):
                continue  # belongs to a nested loop; that loop will report it
            if isinstance(node, ast.Call) and _is_trivial_call(node):
                continue
            if not ctx.is_pure(node):
                continue
            if ctx.read_names(node) & rewritten:
                continue
            if any(_contains(outer, node) for outer in reported):
                continue  # already covered by a larger invariant expression
            reported.append(node)
            yield _evidence(
                unit, "loop_invariant_expression", node, ("C3.S2",),
                f"`{ast.unparse(node)}` does not change across loop iterations "
                f"but is re-evaluated every time",
                expression=ast.unparse(node),
                loop_line=loop.lineno,
                depth=ctx.loop_depth(node),
                strength=Strength.LIKELY,
            )


def _is_trivial_call(call: ast.Call) -> bool:
    """`len(x)` on a rewritten name is the point; `int()` on a literal is not."""
    return not call.args and not call.keywords


def _contains(outer: ast.AST, inner: ast.AST) -> bool:
    """Whether `inner` is a sub-expression of `outer`."""
    return any(node is inner for node in ast.walk(outer))


def string_concat_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """`s += ...` inside a loop -- but only quadratic for some accumulators.

    The textbook version of this rule is wrong on CPython, and measurement says
    so.  When the accumulator is a plain local whose reference count is one,
    CPython resizes the string in place instead of copying it, and the loop is
    already linear: at 20k iterations `out += s` took 2.9 ms against 24 ms for
    the same loop writing through an attribute.  Replacing it with a list and a
    join measured *slower* (62 ms vs 56 ms at 400k).

    The optimisation cannot fire when a second reference to the string exists,
    so the accumulator's assignment target is what decides:

        out += part              plain local, refcount 1  -> linear, not a smell
        self.buf += part         attribute, refcount > 1  -> quadratic
        d["k"] += part           subscript                -> quadratic
        out += part; keep(out)   a reference escapes      -> quadratic

    Numeric accumulators are excluded throughout: `n += 1` is fine.
    """
    for node, enclosing in ctx.inside_loops():
        if not isinstance(node, ast.AugAssign) or not isinstance(node.op, ast.Add):
            continue
        if not _looks_stringy(node.value):
            continue
        loop = enclosing[-1]
        target = node.target
        if isinstance(target, (ast.Attribute, ast.Subscript)):
            yield _evidence(
                unit, "string_concat_in_loop", node, ("C10.S4",),
                f"`{_target_name(target)}` is grown by string concatenation "
                f"inside a loop; because it is stored through "
                f"{'an attribute' if isinstance(target, ast.Attribute) else 'a subscript'}"
                f", CPython cannot resize it in place and copies the whole "
                f"string every iteration",
                accumulator=_target_name(target),
                accumulator_kind="aliased",
                loop_line=loop.lineno,
                strength=Strength.DEFINITE,
            )
        elif isinstance(target, ast.Name):
            escapes = _name_is_read_in(loop, target.id)
            if escapes:
                yield _evidence(
                    unit, "string_concat_in_loop", node, ("C10.S4",),
                    f"`{target.id}` is grown by string concatenation inside a "
                    f"loop and is also read there, so a second reference "
                    f"exists and each iteration copies the whole string",
                    accumulator=target.id,
                    accumulator_kind="escaping",
                    loop_line=loop.lineno,
                    strength=Strength.DEFINITE,
                )
            else:
                yield _evidence(
                    unit, "string_concat_in_loop", node, ("C10.S4",),
                    f"`{target.id}` is grown by string concatenation inside a "
                    f"loop, but it is a plain local with no other reference, "
                    f"so CPython resizes it in place and the loop is already "
                    f"linear -- reject unless this runs on another runtime",
                    accumulator=target.id,
                    accumulator_kind="local",
                    loop_line=loop.lineno,
                    strength=Strength.CONTEXTUAL,
                )


def _target_name(node: ast.AST) -> str:
    """Readable name for an assignment target, for the evidence message."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_target_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return f"{_target_name(node.value)}[...]"
    return "the accumulator"


def _name_is_read_in(loop: ast.AST, name: str) -> bool:
    """Whether `name` is loaded anywhere in the loop, not just assigned to.

    An augmented assignment stores to its target, so any *load* of the same
    name inside the loop means a second reference is taken -- which is exactly
    what stops CPython from resizing the string in place.
    """
    return any(
        isinstance(node, ast.Name)
        and node.id == name
        and isinstance(node.ctx, ast.Load)
        for node in ast.walk(loop)
    )


def _looks_stringy(node: ast.AST) -> bool:
    """Best-effort check that an expression produces text."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.JoinedStr):  # f-string
        return True
    if isinstance(node, ast.BinOp):
        return _looks_stringy(node.left) or _looks_stringy(node.right)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in {"str", "repr", "format", "chr"}:
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"join", "format", "strip"}:
            return True
    return False


def repeated_lookup_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Attribute chains or globals resolved repeatedly inside a loop body.

    Each `a.b.c` costs a dict lookup per level, and each global costs a scope
    chain walk.  Only chains of depth >= 2 that appear more than once and are
    never rewritten in the loop are reported.
    """
    for loop in ctx.loops:
        rewritten = ctx.assigned_names(loop)
        seen: dict[str, list[ast.AST]] = {}
        for node in ast.walk(loop):
            if not isinstance(node, ast.Attribute) or not isinstance(node.ctx, ast.Load):
                continue
            chain = _attribute_chain(node)
            if chain is None or chain.count(".") < 1:
                continue
            if chain.split(".")[0] in rewritten:
                continue
            seen.setdefault(chain, []).append(node)

        for chain, nodes in seen.items():
            if len(nodes) < 2:
                continue
            yield _evidence(
                unit, "repeated_lookup_in_loop", nodes[0], ("C8.S3", "C10.S5"),
                f"`{chain}` is resolved {len(nodes)} times inside the loop; each "
                f"access walks the attribute chain again",
                chain=chain,
                occurrences=len(nodes),
                loop_line=loop.lineno,
                strength=Strength.CONTEXTUAL,
            )


def _attribute_chain(node: ast.Attribute) -> str | None:
    """Render `a.b.c` as a string, or None if the base is not a plain name."""
    parts = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def membership_test_on_sequence(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """`x in some_list` inside a loop: linear scan where a set would be O(1)."""
    for node, enclosing in ctx.inside_loops():
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], (ast.In, ast.NotIn)):
            continue
        haystack = node.comparators[0]
        if not _is_sequence_valued(haystack, ctx):
            continue
        yield _evidence(
            unit, "membership_test_on_sequence", node, ("C5.S1", "C5.S2", "C3.S4"),
            f"membership test `{ast.unparse(node)}` scans a sequence linearly "
            f"on every iteration; a set or dict index would be constant-time",
            haystack=ast.unparse(haystack),
            loop_line=enclosing[-1].lineno,
            strength=Strength.LIKELY,
        )


def _is_sequence_valued(node: ast.AST, ctx: UnitContext) -> bool:
    """Whether an expression plausibly holds a list/tuple rather than a set/dict."""
    if isinstance(node, (ast.List, ast.Tuple, ast.ListComp)):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in {"list", "tuple", "sorted"}
    if isinstance(node, ast.Name):
        return _binds_sequence(node.id, ctx)
    return False


def _binds_sequence(name: str, ctx: UnitContext) -> bool:
    """Look for an assignment in the unit that gives `name` a list/tuple value."""
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if name in targets and _is_literal_sequence(node.value):
            return True
    return False


def _is_literal_sequence(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Tuple, ast.ListComp)):
        return True
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "tuple", "sorted"}
    )


def nested_loops(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Loop nests of depth >= 2, which are quadratic or worse in their inputs."""
    for loop in ctx.loops:
        depth = ctx.loop_depth(loop) + 1
        if depth < 2:
            continue
        if any(isinstance(inner, LOOP_NODES) for inner in ast.iter_child_nodes(loop)):
            continue  # report at the innermost loop only
        outer = ctx.loops_around(loop)
        yield _evidence(
            unit, "nested_loops", loop, ("C3.S4", "C7.S1"),
            f"loop nest {depth} levels deep; total work grows as the product of "
            f"the iteration counts",
            depth=depth,
            outer_lines=[getattr(o, "lineno", 0) for o in outer],
            strength=Strength.CONTEXTUAL,
        )


def construction_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Containers, lambdas or comprehensions built fresh on every iteration."""
    for loop in ctx.loops:
        for node in ast.iter_child_nodes(loop):
            for sub in ast.walk(node):
                if ctx.loops_around(sub)[-1:] != (loop,):
                    continue
                kind = _construction_kind(sub)
                if kind is None:
                    continue
                yield _evidence(
                    unit, "construction_in_loop", sub, ("C3.S3", "C6.S1"),
                    f"a new {kind} is created on every iteration; if it does not "
                    f"escape the iteration it can be hoisted or reused",
                    construct=kind,
                    loop_line=loop.lineno,
                    strength=Strength.LIKELY,
                )


def _construction_kind(node: ast.AST) -> str | None:
    if isinstance(node, ast.Lambda):
        return "lambda"
    if isinstance(node, COMPREHENSION_NODES):
        return "comprehension"
    if isinstance(node, (ast.List, ast.Dict, ast.Set)) and _has_elements(node):
        return "container literal"
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in CONSTRUCTOR_NAMES
    ):
        return f"{node.func.id}()"
    return None


def _has_elements(node: ast.AST) -> bool:
    if isinstance(node, ast.Dict):
        return bool(node.keys)
    return bool(getattr(node, "elts", []))


def index_based_iteration(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """`for i in range(len(xs))` where the index is only used to read `xs[i]`."""
    for loop in ctx.loops:
        if not isinstance(loop, ast.For) or not isinstance(loop.target, ast.Name):
            continue
        sequence = _range_len_argument(loop.iter)
        if sequence is None:
            continue
        index = loop.target.id
        subscripts = [
            node for node in ast.walk(loop)
            if isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Name)
            and node.slice.id == index
        ]
        if not subscripts:
            continue
        yield _evidence(
            unit, "index_based_iteration", loop, ("C3.S1",),
            f"iterating `range(len({sequence}))` and indexing back into it; "
            f"iterating the sequence directly avoids an index lookup per item",
            sequence=sequence,
            index=index,
            strength=Strength.LIKELY,
        )


def _range_len_argument(node: ast.AST) -> str | None:
    """Return `xs` for an iterable expression of the form `range(len(xs))`."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        return None
    if node.func.id != "range" or len(node.args) != 1:
        return None
    inner = node.args[0]
    if not (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)):
        return None
    if inner.func.id != "len" or len(inner.args) != 1:
        return None
    return ast.unparse(inner.args[0])


def append_only_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A loop whose whole body is one `.append()`: a comprehension in disguise."""
    for loop in ctx.loops:
        if not isinstance(loop, ast.For) or loop.orelse or len(loop.body) != 1:
            continue
        statement = loop.body[0]
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not (isinstance(call.func, ast.Attribute) and call.func.attr == "append"):
            continue
        yield _evidence(
            unit, "append_only_loop", loop, ("C3.S1", "C10.S3"),
            "loop body is a single `.append()`; a comprehension does the same "
            "work without a bound-method lookup and call per item",
            target=ast.unparse(call.func.value),
            strength=Strength.LIKELY,
        )


def missing_early_exit(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A search loop that sets a conclusive flag but keeps iterating.

    Looks for a loop containing an `if` whose body only assigns a constant and
    which contains no `break` or `return` anywhere -- the classic "found it,
    but carry on scanning" shape.
    """
    for loop in ctx.loops:
        if _contains_exit(loop):
            continue
        conclusive = [
            node for node in ast.walk(loop)
            if isinstance(node, ast.If) and _assigns_only_constants(node.body)
        ]
        if not conclusive:
            continue
        yield _evidence(
            unit, "missing_early_exit", conclusive[0], ("C3.S5",),
            "the loop reaches a conclusive result but continues iterating; "
            "no `break` or `return` leaves the loop",
            loop_line=loop.lineno,
            strength=Strength.LIKELY,
        )


def _contains_exit(loop: ast.AST) -> bool:
    """Whether the loop can terminate early, ignoring nested loops' breaks."""
    for node in ast.walk(loop):
        if isinstance(node, ast.Return):
            return True
        if isinstance(node, ast.Break):
            return True
    return False


def _assigns_only_constants(body: list[ast.stmt]) -> bool:
    return bool(body) and all(
        isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Constant)
        for statement in body
    )


def try_except_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Exception handling on the per-iteration path.

    Cheap when exceptions are rare, expensive when they are the common case --
    which of the two applies is exactly what the reader has to decide.
    """
    for node, enclosing in ctx.inside_loops():
        if isinstance(node, ast.Try):
            yield _evidence(
                unit, "try_except_in_loop", node, ("C4.S6", "C3.S3"),
                "try/except sits on the per-iteration path; if the exception is "
                "the common case, each raise allocates and unwinds",
                loop_line=enclosing[-1].lineno,
                handlers=[ast.unparse(h.type) if h.type else "bare" for h in node.handlers],
                strength=Strength.CONTEXTUAL,
            )


def regex_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Regex work inside a loop, where the pattern could be compiled once.

    Suggests both C3.S3 and C8.S2: hoisting to the enclosing function is the
    former, hoisting to module scope so it survives across calls is the latter.
    """
    for node, enclosing in ctx.inside_loops():
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        base = node.func.value
        if not isinstance(base, ast.Name):
            continue
        if (base.id, node.func.attr) not in COMPILE_CALLS:
            continue
        yield _evidence(
            unit, "regex_in_loop", node, ("C3.S3", "C8.S2"),
            f"`{base.id}.{node.func.attr}()` is called inside a loop; the "
            f"pattern is re-resolved on every iteration",
            call=f"{base.id}.{node.func.attr}",
            loop_line=enclosing[-1].lineno,
            strength=Strength.LIKELY,
        )


def mutation_during_iteration(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Mutating the very collection a `for` loop is walking."""
    for loop in ctx.loops:
        if not isinstance(loop, ast.For) or not isinstance(loop.iter, ast.Name):
            continue
        iterated = loop.iter.id
        for node in ast.walk(loop):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"append", "remove", "insert", "pop", "extend", "clear"}:
                continue
            if not (isinstance(node.func.value, ast.Name) and node.func.value.id == iterated):
                continue
            yield _evidence(
                unit, "mutation_during_iteration", node, ("C3.S7",),
                f"`{iterated}` is mutated with `.{node.func.attr}()` while being "
                f"iterated, which skips elements or grows the loop unboundedly",
                collection=iterated,
                operation=node.func.attr,
                strength=Strength.DEFINITE,
            )


RULES = [
    loop_invariant_expression,
    string_concat_in_loop,
    repeated_lookup_in_loop,
    membership_test_on_sequence,
    nested_loops,
    construction_in_loop,
    index_based_iteration,
    append_only_loop,
    missing_early_exit,
    try_except_in_loop,
    regex_in_loop,
    mutation_during_iteration,
]
