"""Analyzers for control flow, reuse, call overhead and external access.

These cover the root causes that are not specifically about loop bodies or
allocation: branch shape (C4), missing reuse across calls (C8), call overhead
(C2), external I/O (C9) and concurrency (C11).
"""

from __future__ import annotations

import ast
from typing import Iterator

from ..models import Evidence, Strength, UnitRef
from ..context import OPAQUE_NODES, UnitContext

# Calls that reach outside the process. Cheap once, ruinous per iteration.
#
# Split in two, because method names are not evidence on their own. `.get()` is
# `dict.get` far more often than it is an HTTP request; `.update()` is a dict
# and a set before it is a database; `.insert()` is `list.insert`. Firing on
# the bare name produced eight hits on a pure-Python call-graph module that
# performs no I/O at all, which is the kind of noise that teaches a reader to
# skip the rule -- and a rule nobody reads is worse than no rule.
UNAMBIGUOUS_IO_CALLS = frozenset({
    "urlopen", "recv", "recvfrom", "sendall", "executemany",
    "fetchone", "fetchall", "fetchmany", "commit", "rollback", "writelines",
})
"""Names that essentially never mean anything but I/O."""

AMBIGUOUS_IO_CALLS = frozenset({
    "get", "post", "put", "delete", "patch", "head", "request", "fetch",
    "execute", "query", "save", "insert", "update", "read", "write", "send",
    "open", "connect", "close", "download", "upload",
})
"""Names that mean I/O only when the receiver is one of the objects below."""

IO_RECEIVERS = frozenset({
    "conn", "connection", "cur", "cursor", "db", "database", "session",
    "client", "sock", "socket", "requests", "http", "httpx", "urllib",
    "response", "resp", "channel", "stream", "s3", "bucket", "redis",
    "api", "service", "engine", "pool", "transport", "ftp", "smtp", "ssh",
    "file", "fh", "fp", "handle", "writer", "reader", "queryset", "objects",
})
"""Receiver names that mark an object as living outside the process.

Matched on the identifier, and on the last segment of a dotted receiver, so
`self.conn.execute(...)` counts and `self.rows.get(...)` does not. Crude, and
deliberately so: the alternative is type inference, and a rule that guesses
types wrongly is worse than one that admits it only recognises the obvious.

`cache` was here and had to go. It reads like a remote store and is a local
dict far more often, so `cache.get(key)` in a loop -- the exact false positive
this split was built to stop -- came straight back through the receiver list.
"""

IO_MODULES = frozenset({
    "requests", "httpx", "urllib", "socket", "sqlite3", "psycopg2", "pymysql",
    "boto3", "redis", "aiohttp", "http", "ftplib", "smtplib", "paramiko",
})
"""Imports that make a name in this file plausible as an I/O handle."""

LOCK_METHODS = frozenset({"acquire"})
"""`release` was here too, so an explicit acquire/release pair around one
loop body was reported twice -- and releasing a lock is not what costs."""

# Loop shapes that a single builtin already implements in C.
BUILTIN_EQUIVALENTS = {
    "max": "a running maximum",
    "min": "a running minimum",
    "sum": "a running total",
}

MAX_NESTING_DEPTH = 4

# Definitions whose insides belong to their own unit, not the enclosing one.
NESTING_OPAQUE = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)

# Calls cheap enough that putting them first in a boolean chain costs nothing.
# Without this exclusion the short-circuit rule fires on almost every guard
# clause in real code: `isinstance(x, T) and x.flag` is idiomatic, not a smell.
CHEAP_CALLS = frozenset({
    "isinstance", "issubclass", "len", "type", "id", "bool", "hasattr",
    "callable", "getattr", "int", "str", "float", "abs", "ord", "chr",
})

# Repeating one of these costs almost nothing, so seeing it twice in a scope is
# not worth reporting as redundant computation.
TRIVIAL_CALLS = CHEAP_CALLS | {"list", "dict", "set", "tuple", "repr"}

MIN_REPEATED_CALLS = 3


def _evidence(unit: UnitRef, kind: str, node: ast.AST, suggests: tuple[str, ...],
              message: str, strength: Strength = Strength.LIKELY, **detail) -> Evidence:
    return Evidence(
        kind=kind, unit=unit, lineno=getattr(node, "lineno", unit.lineno),
        suggests=suggests, message=message, strength=strength, detail=detail,
    )


# -- control flow ---------------------------------------------------------


def independent_exclusive_ifs(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Consecutive `if`s testing the same variable against different constants.

    Written as separate statements, every condition is evaluated on every pass.
    An `elif` chain stops at the first match.
    """
    for node in ast.walk(ctx.node):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        run: list[ast.If] = []
        for statement in body:
            if isinstance(statement, ast.If) and not statement.orelse:
                subject = _compared_subject(statement.test)
                if subject and (not run or _compared_subject(run[0].test) == subject):
                    run.append(statement)
                    continue
            if _is_chainable(run, ctx):
                yield _exclusive_ifs_evidence(unit, run)
            run = []
        if _is_chainable(run, ctx):
            yield _exclusive_ifs_evidence(unit, run)


def _is_chainable(run: list[ast.If], ctx: UnitContext) -> bool:
    """Whether turning `run` into an `elif` chain would preserve behaviour and save tests.

    Three shapes used to be reported and are not findings, all of them from the
    card's own counter-examples:

      * a body that rebinds the subject, so the later tests ask about a
        different value and chaining them drops behaviour;
      * arms that all return or raise, where control already never reaches the
        later tests after a match, so `elif` changes only the punctuation;
      * the same constant tested twice, which is not exclusive at all.
    """
    if len(run) < 2:
        return False
    if len({_compared_constant(arm.test) for arm in run}) != len(run):
        return False
    root = _compared_subject(run[0].test).split(".")[0]
    if any(root in ctx.assigned_names(arm) for arm in run):
        return False
    return not all(_exits(arm.body) for arm in run[:-1])


def _exits(body: list[ast.stmt]) -> bool:
    """Whether a branch body always leaves the enclosing run."""
    return bool(body) and isinstance(body[-1], (ast.Return, ast.Raise, ast.Continue, ast.Break))


def _compared_constant(test: ast.AST) -> object:
    return ast.unparse(test.comparators[0]) if isinstance(test, ast.Compare) else None


def _exclusive_ifs_evidence(unit: UnitRef, run: list[ast.If]) -> Evidence:
    subject = _compared_subject(run[0].test)
    return _evidence(
        unit, "independent_exclusive_ifs", run[0], ("C4.S4",),
        f"{len(run)} separate `if` statements all test `{subject}`; every one is "
        f"evaluated even after an earlier branch has already matched",
        subject=subject, count=len(run),
        strength=Strength.LIKELY,
    )


def _compared_subject(test: ast.AST) -> str | None:
    """The left-hand side of a simple `x == const` comparison.

    Equality against distinct constants is the only shape that is exclusive by
    construction. Ordering comparisons used to count as well, which reported
    `if usage > 90: page()` followed by `if usage > 75: warn()` -- overlapping
    ranges where both arms are meant to run.
    """
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return None
    if not isinstance(test.ops[0], ast.Eq):
        return None
    if not all(isinstance(c, ast.Constant) for c in test.comparators):
        return None
    return ast.unparse(test.left) if isinstance(test.left, (ast.Name, ast.Attribute)) else None


def expensive_operand_first(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A call placed before a cheap test in an `and`/`or` chain.

    Short-circuit evaluation can only skip work that comes *after* the operand
    that decides the result, so putting the expensive operand first forfeits it.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.BoolOp) or len(node.values) < 2:
            continue
        for position, operand in enumerate(node.values[:-1]):
            if not _contains_expensive_call(operand):
                continue
            # A later operand that reads a name an earlier one binds cannot be
            # promoted past it: `(row := load_row(x)) and row.active` used to be
            # reported, and there `row` does not exist until the call has run.
            bound = _walrus_targets(node.values[: position + 1])
            cheaper = [
                v for v in node.values[position + 1 :]
                if not _contains_call(v) and not (ctx.read_names(v) & bound)
            ]
            if not cheaper:
                continue
            yield _evidence(
                unit, "expensive_operand_first", node, ("C4.S1",),
                f"`{ast.unparse(operand)}` calls a function before the cheaper "
                f"test `{ast.unparse(cheaper[0])}`, so short-circuiting cannot "
                f"skip the call",
                expensive=ast.unparse(operand), cheap=ast.unparse(cheaper[0]),
                strength=Strength.CONTEXTUAL,
            )
            break


def _contains_call(node: ast.AST) -> bool:
    return any(isinstance(sub, ast.Call) for sub in ast.walk(node))


def _walrus_targets(operands: list[ast.AST]) -> set[str]:
    """Names bound by `:=` anywhere in these operands."""
    return {
        sub.target.id
        for operand in operands
        for sub in ast.walk(operand)
        if isinstance(sub, ast.NamedExpr) and isinstance(sub.target, ast.Name)
    }


def _contains_expensive_call(node: ast.AST) -> bool:
    """A call that is not one of the recognisably cheap builtins."""
    return any(
        isinstance(sub, ast.Call)
        and not (isinstance(sub.func, ast.Name) and sub.func.id in CHEAP_CALLS)
        for sub in ast.walk(node)
    )


def deep_conditional_nesting(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Branches nested deeply enough that guard clauses would flatten them."""
    deepest, depth = _deepest_if(ctx.node, 0)
    if depth > MAX_NESTING_DEPTH and deepest is not None:
        yield _evidence(
            unit, "deep_conditional_nesting", deepest, ("C4.S3",),
            f"conditionals nested {depth} levels deep; every level re-tests on "
            f"the way to the work at the bottom",
            depth=depth,
            strength=Strength.CONTEXTUAL,
        )


def _deepest_if(node: ast.AST, depth: int) -> tuple[ast.AST | None, int]:
    """Deepest `if` under `node`, and how many `if` levels enclose it.

    Two shapes used to be counted as nesting and are not. An `elif` arm is a
    separate `ast.If` in the parent's `orelse`, so a six-arm chain measured as
    depth six -- but a chain is a linear search, not a nest, and no path
    evaluates all of it. And a nested `def` is its own unit: counting its
    nesting here as well reported the same lines against two units.
    """
    best_node: ast.AST | None = None
    best_depth = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, NESTING_OPAQUE):
            continue
        child_depth = depth
        if isinstance(child, ast.If) and not _is_chained_arm(node, child):
            child_depth = depth + 1
            if child_depth > best_depth:
                best_node, best_depth = child, child_depth
        found_node, found_depth = _deepest_if(child, child_depth)
        if found_depth > best_depth:
            best_node, best_depth = found_node, found_depth
    return best_node, best_depth


def _is_chained_arm(parent: ast.AST, child: ast.If) -> bool:
    """Whether `child` is the `elif` of `parent` rather than a level inside it."""
    return isinstance(parent, ast.If) and parent.orelse == [child]


# -- reuse ----------------------------------------------------------------


def recursion_without_memo(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A function that calls itself more than once with no caching decorator.

    Two self-calls on the same path means the recursion tree re-solves
    overlapping subproblems, which is the shape memoization exists for.  A
    single self-call is ordinary linear recursion and is reported separately.
    """
    if not isinstance(ctx.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    name = ctx.node.name
    self_calls = [
        node for node in ast.walk(ctx.node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    ]
    if not self_calls or _has_cache_decorator(ctx.node):
        return

    # One self-call *inside a loop* is a tree walk: each child is a distinct
    # subproblem, so nothing overlaps and there is nothing to memoise -- and it
    # is not linear recursion either, which is C7.S3's own counter-example
    # (an explicit stack would just reimplement the call stack in Python).
    if len(self_calls) == 1 and ctx.in_loop(self_calls[0]):
        return

    if len(self_calls) >= 2:
        yield _evidence(
            unit, "recursion_without_memo", self_calls[0], ("C7.S2", "C8.S1"),
            f"`{name}` calls itself {len(self_calls)} times and is not cached, so "
            f"overlapping subproblems are recomputed",
            self_calls=len(self_calls),
            strength=Strength.LIKELY,
        )
    else:
        yield _evidence(
            unit, "linear_recursion", self_calls[0], ("C7.S3",),
            f"`{name}` recurses once per call; CPython builds a frame per level "
            f"and does not optimise tail calls",
            self_calls=1,
            strength=Strength.CONTEXTUAL,
        )


def _has_cache_decorator(node: ast.AST) -> bool:
    names = {
        ast.unparse(d).split("(")[0].split(".")[-1]
        for d in getattr(node, "decorator_list", [])
    }
    return bool(names & {"cache", "lru_cache", "cached_property", "memoize"})


def repeated_pure_call(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """The same pure call appearing more than once outside any loop.

    Within a loop this is C3.S2 and the loop analyzer already reports it, so
    this rule deliberately looks only at straight-line code (C1.S4).
    """
    seen: dict[str, list[ast.Call]] = {}
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Call) or ctx.in_loop(node):
            continue
        if not node.args or not _repeatable(node, ctx):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in TRIVIAL_CALLS:
            continue  # recomputing len(x) twice is not worth a claim
        seen.setdefault(ast.unparse(node), []).append(node)

    for expression, calls in seen.items():
        if len(calls) < MIN_REPEATED_CALLS:
            continue
        yield _evidence(
            unit, "repeated_pure_call", calls[0], ("C1.S4",),
            f"`{expression}` is computed {len(calls)} times in the same scope "
            f"with nothing changing in between",
            expression=expression, occurrences=len(calls),
            strength=Strength.CONTEXTUAL,
        )


def _repeatable(call: ast.Call, ctx: UnitContext) -> bool:
    """Whether recomputing this call is plausibly redundant rather than required.

    `is_pure` only trusts builtins and known-safe methods, and gating on it
    alone made this rule almost unreachable: `parse_manifest(path)` three times
    in one function -- exactly what C1.S4 is about -- is a call to a plain
    function, which nothing can prove pure.  So a bare-name call with arguments
    counts, and the evidence stays `contextual` with the reader asked to confirm
    it has no side effect.

    Method calls stay restricted to the recognised-pure set.  `session.get(k)`
    repeated three times is a real finding and it is C8.S4, not this one.
    """
    if ctx.is_pure(call):
        return True
    return isinstance(call.func, ast.Name) and all(
        isinstance(argument, (ast.Name, ast.Constant, ast.Attribute))
        for argument in call.args
    ) and not call.keywords


def manual_builtin_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A loop hand-rolling `max`, `min` or `sum` over its iterable."""
    for loop in ctx.loops:
        # The tracking has to be the whole body. A loop that also records every
        # prefix maximum computes a running series, and no single `max()` call
        # replaces it -- reporting one was telling the reader to delete output.
        if not isinstance(loop, ast.For) or len(loop.body) != 1:
            continue
        for node in loop.body:
            builtin = _hand_rolled_builtin(node)
            if builtin is None:
                continue
            yield _evidence(
                unit, "manual_builtin_loop", loop, ("C10.S1",),
                f"the loop maintains {BUILTIN_EQUIVALENTS[builtin]} by hand; "
                f"`{builtin}()` does this in C",
                builtin=builtin,
                strength=Strength.LIKELY,
            )
            break


def _hand_rolled_builtin(node: ast.AST) -> str | None:
    """Detect `if x > best: best = x` and `total += x` loop bodies.

    The `None`-guarded form counts too.  Starting an extreme at `None` and
    writing `if best is None or x < best:` is at least as common as seeding it
    from the first element, and requiring a bare comparison missed all of it.
    The repair there needs `min(..., default=None)` to keep the empty case.
    """
    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
        return "sum"
    if not isinstance(node, ast.If) or len(node.body) != 1 or node.orelse:
        return None
    if not isinstance(node.body[0], ast.Assign):
        return None
    return _extreme_from(node.test)


def _extreme_from(test: ast.AST) -> str | None:
    """`max` or `min` for a comparison, seeing through a `None` guard."""
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        found = [_extreme_from(value) for value in test.values]
        named = [name for name in found if name]
        return named[0] if len(named) == 1 else None
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return None
    operator = test.ops[0]
    if isinstance(operator, (ast.Gt, ast.GtE)):
        return "max"
    if isinstance(operator, (ast.Lt, ast.LtE)):
        return "min"
    return None


# -- call overhead --------------------------------------------------------


def method_ignores_self(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """An instance method that never touches `self`.

    Each call still builds a bound method object.  `@staticmethod` or a plain
    module-level function skips that.
    """
    if unit.kind != "method" or not isinstance(ctx.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    arguments = ctx.node.args.args
    if not arguments or arguments[0].arg != "self":
        return
    # Dunders, decorated methods and abstract stubs all have to keep their
    # signature: making them static would break the protocol they implement.
    if ctx.node.name.startswith("__") or ctx.node.decorator_list:
        return
    if _is_abstract_body(ctx.node.body):
        return
    if "self" in ctx.read_names(ctx.node):
        return
    yield _evidence(
        unit, "method_ignores_self", ctx.node, ("C2.S2",),
        f"`{ctx.node.name}` never uses `self`, so every call builds a bound "
        f"method object for nothing",
        method=ctx.node.name,
        strength=Strength.CONTEXTUAL,
    )


def trivial_delegation(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A function whose entire body forwards its own arguments to one call.

    Restricted to *pure* forwarding -- same arguments, in the same order, with
    nothing added.  Anything looser fires on most of a library's public API,
    where a thin named wrapper is deliberate design rather than waste.  Even
    so this stays contextual: it only costs energy on a hot path.
    """
    if not isinstance(ctx.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    if ctx.node.name.startswith("__") or ctx.node.decorator_list:
        return
    body = [s for s in ctx.node.body if not _is_docstring(s)]
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return
    value = body[0].value
    if not isinstance(value, ast.Call) or not _forwards_arguments(ctx.node, value):
        return
    yield _evidence(
        unit, "trivial_delegation", ctx.node, ("C2.S1",),
        f"`{ctx.node.name}` only forwards to `{ast.unparse(value.func)}`, adding "
        f"a stack frame per call without adding behaviour",
        delegate=ast.unparse(value.func),
        strength=Strength.CONTEXTUAL,
    )


def _forwards_arguments(function: ast.AST, call: ast.Call) -> bool:
    """Whether `call` passes exactly the function's own parameters, in order.

    A parameterless wrapper counts.  `def count(self): return
    self._backend.count()` is as pure a forward as one that passes arguments,
    and requiring at least one parameter dropped the whole family.
    """
    if call.keywords:
        return False
    parameters = [a.arg for a in function.args.args if a.arg != "self"]
    passed = [a.id for a in call.args if isinstance(a, ast.Name)]
    return len(passed) == len(call.args) and passed == parameters


def _is_abstract_body(body: list[ast.stmt]) -> bool:
    """Whether a body is just `pass`, `...` or `raise NotImplementedError`."""
    statements = [s for s in body if not _is_docstring(s)]
    if len(statements) != 1:
        return False
    only = statements[0]
    if isinstance(only, ast.Pass):
        return True
    if isinstance(only, ast.Expr) and isinstance(only.value, ast.Constant):
        return only.value.value is Ellipsis
    return isinstance(only, ast.Raise) and "NotImplementedError" in ast.unparse(only)


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _has_any_decorator(node: ast.AST, names: set[str]) -> bool:
    present = {
        ast.unparse(d).split("(")[0].split(".")[-1]
        for d in getattr(node, "decorator_list", [])
    }
    return bool(present & names)


# -- external access and concurrency --------------------------------------


def io_call_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A call that leaves the process, made once per iteration.

    Suggests both fragmented I/O (C9.S1) and the N+1 retrieval pattern (C9.S3);
    which one applies depends on whether the calls are independent or each
    depends on the previous result.

    An unambiguous method name is enough on its own. An ambiguous one has to be
    called on something that looks like it lives outside the process -- see
    `IO_RECEIVERS` for why that test is a name match rather than a type.
    """
    for node in ctx.own_nodes():
        if not ctx.repeats(node):
            continue
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if _dispatched_concurrently(node, ctx):
            continue
        name = node.func.attr
        if name in UNAMBIGUOUS_IO_CALLS:
            confidence = Strength.LIKELY
        elif name in AMBIGUOUS_IO_CALLS and _is_io_receiver(node.func.value, ctx):
            confidence = Strength.CONTEXTUAL
        else:
            continue
        yield _evidence(
            unit, "io_call_in_loop", node, ("C9.S1", "C9.S3"),
            f"`{ast.unparse(node.func)}()` looks like it leaves the process, and "
            f"it runs once per iteration; batching would amortise the round trip",
            call=name,
            loop_line=getattr(ctx.repeats_around(node)[-1], "lineno", unit.lineno),
            strength=confidence,
        )


CONCURRENT_DISPATCH = frozenset({
    "gather", "wait", "as_completed", "create_task", "ensure_future",
    "map", "starmap", "imap", "imap_unordered", "submit", "wait_for",
})


def _dispatched_concurrently(call: ast.Call, ctx: UnitContext) -> bool:
    """Whether the comprehension holding `call` is handed to a concurrent runner.

    `asyncio.gather(*(session.get(u) for u in urls))` is what this rule asks
    for, so reporting it would send a reader to repair code that is already
    repaired.  The round trips still happen once per element, but they overlap,
    which is the whole of C9.S1's advice.

    Two shapes reach a runner and both are found by walking outwards: the
    dispatcher may wrap the whole comprehension, as `gather` does, or wrap each
    call inside it, as `create_task` does.  A statement loop that awaits in
    place has no such ancestor and is still reported.
    """
    node: ast.AST | None = ctx.parent_of(call)
    while node is not None and not isinstance(node, OPAQUE_NODES):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name in CONCURRENT_DISPATCH:
                return True
        node = ctx.parent_of(node)
    return False


def _is_io_receiver(node: ast.AST, ctx: UnitContext) -> bool:
    """Whether an expression plausibly holds something outside the process.

    Checks the last name in the receiver, so `self.db.execute` and
    `self._conn.execute` both count while `self.rows.get` does not, and treats
    any name bound from an I/O module as a handle.
    """
    if isinstance(node, ast.Attribute):
        return node.attr.lower().lstrip("_") in IO_RECEIVERS
    if isinstance(node, ast.Call):
        return _is_io_receiver(node.func, ctx)
    if not isinstance(node, ast.Name):
        return False
    if node.id.lower().lstrip("_") in IO_RECEIVERS:
        return True
    origin = ctx.imports.get(node.id, "")
    return origin.split(".")[0] in IO_MODULES


def lock_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Lock acquisition on the per-iteration path."""
    for node, enclosing in ctx.inside_loops():
        acquired = (
            isinstance(node, (ast.With, ast.AsyncWith))
            and any(_looks_like_lock(item.context_expr) for item in node.items)
        ) or (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in LOCK_METHODS
            and _looks_like_lock(node.func.value)
        )
        if not acquired:
            continue
        yield _evidence(
            unit, "lock_in_loop", node, ("C11.S1", "C11.S2"),
            "a lock is acquired on every iteration, serialising work that "
            "may not need to be serialised",
            loop_line=enclosing[-1].lineno,
            strength=Strength.CONTEXTUAL,
        )


def _looks_like_lock(node: ast.AST) -> bool:
    text = ast.unparse(node).lower()
    return "lock" in text or "semaphore" in text or "mutex" in text


RULES = [
    independent_exclusive_ifs,
    expensive_operand_first,
    deep_conditional_nesting,
    recursion_without_memo,
    repeated_pure_call,
    manual_builtin_loop,
    method_ignores_self,
    trivial_delegation,
    io_call_in_loop,
    lock_in_loop,
]
