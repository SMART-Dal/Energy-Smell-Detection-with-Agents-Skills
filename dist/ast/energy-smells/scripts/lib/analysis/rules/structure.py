"""Analyzers for control flow, reuse, call overhead and external access.

These cover the root causes that are not specifically about loop bodies or
allocation: branch shape (C4), missing reuse across calls (C8), call overhead
(C2), external I/O (C9) and concurrency (C11).
"""

from __future__ import annotations

import ast
import re
from typing import Iterator

from ..models import Evidence, UnitRef
from ..context import LOOP_NODES, OPAQUE_NODES, UnitContext, is_cheap_expression

# Calls that reach outside the process. Cheap once, ruinous per iteration.
#
# Split in two, because method names are not evidence on their own. `.get()` is
# `dict.get` far more often than it is an HTTP request; `.update()` is a dict
# and a set before it is a database; `.insert()` is `list.insert`. Firing on
# the bare name produced eight hits on a pure-Python call-graph module that
# performs no I/O at all, which is the kind of noise that teaches a reader to
# skip the rule -- and a rule nobody reads is worse than no rule.
UNAMBIGUOUS_IO_CALLS = frozenset({
    "urlopen", "recv", "recvfrom", "sendall", "writelines",
})
"""Names that essentially never mean anything but I/O."""

DATABASE_CALLS = frozenset({
    "executemany", "fetchone", "fetchall", "fetchmany", "commit", "rollback",
})
"""Database verbs, which need a receiver like the ambiguous ones do.

They were trusted on the name alone, so an in-memory undo buffer's
`buffer.rollback()` and a ring buffer's `fetchone()` were reported as leaving
the process. On a cursor or a connection they still are."""

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
    "callable", "getattr", "int", "str", "float", "abs", "ord", "chr", "super",
})

LOOKUP_METHODS = frozenset({"get", "keys", "values", "items"})

CHEAP_METHODS = LOOKUP_METHODS | frozenset({
    "startswith", "endswith", "isupper", "islower", "isdigit", "isalpha",
    "isalnum", "isspace", "istitle", "isnumeric", "isdecimal", "isidentifier",
    "isascii", "isfinite", "isnan", "isinf",
    "lower", "upper", "casefold", "strip", "lstrip", "rstrip",
    "time", "monotonic", "perf_counter", "time_ns", "monotonic_ns", "perf_counter_ns",
})
"""Methods that cost about what a comparison costs: a dict probe, a view, a
prefix check, a character-class test, a float classification, a case or
whitespace normalisation of what is almost always a short string, or a read
of the clock."""

SAFE_TO_PROMOTE = frozenset({
    "len", "isinstance", "issubclass", "type", "id", "bool", "hasattr", "callable",
})
"""Cheap calls that also cannot raise on whatever a guard was protecting.

`int`, `float` and `ord` are cheap and are the classic thing an earlier
operand exists to guard, so promoting one past its guard trades a saving for
a `ValueError`."""

# Repeating one of these costs almost nothing, so seeing it twice in a scope is
# not worth reporting as redundant computation.
TRIVIAL_CALLS = CHEAP_CALLS | {"list", "dict", "set", "tuple", "repr"} | {
    "defaultdict", "OrderedDict", "Counter", "deque", "bytearray",
}
"""Calls never worth deduplicating: cheap builtins, and constructors whose every
call is meant to build a separate object -- `by_arm = defaultdict(list)` three
times is three dicts, not one computed thrice."""

NONDETERMINISTIC_CALLS = frozenset({
    "random", "randint", "randrange", "choice", "choices", "shuffle", "sample",
    "uniform", "gauss", "randbytes", "getrandbits",
    "next", "input", "time", "monotonic", "perf_counter", "time_ns",
    "now", "today", "utcnow", "uuid1", "uuid4", "token_bytes", "token_hex",
    "token_urlsafe", "urandom", "getpid", "tempfile", "mktemp",
})
"""Bare-name calls that return something different every time.

Caching one is not a saving, it is a behaviour change -- three `randint(1, 6)`
calls are three dice."""

MIN_REPEATED_CALLS = 3


def _evidence(unit: UnitRef, kind: str, node: ast.AST, suggests: tuple[str, ...],
              message: str, **detail) -> Evidence:
    return Evidence(
        kind=kind, unit=unit, lineno=getattr(node, "lineno", unit.lineno),
        suggests=suggests, message=message, detail=detail,
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
    # `if val == 1:` and `if val == True:` render as different source and are
    # the same test -- `1 == True` in Python, and so do `0`/`False` and
    # `1.0`/`1`. Compared by value, `{1, True}` collapses to one element and
    # the run stops being exclusive.
    literals = [arm.test.comparators[0] for arm in run
                if isinstance(arm.test, ast.Compare) and len(arm.test.comparators) == 1]
    if len(literals) == len(run) and all(isinstance(c, ast.Constant) for c in literals):
        try:
            if len({c.value for c in literals}) != len(run):
                return False
        except TypeError:                       # an unhashable literal
            pass
    root = _compared_subject(run[0].test).split(".")[0]
    if any(root in ctx.assigned_names(arm) for arm in run):
        return False
    # `task.state = "RUNNING"` rebinds what the next arm tests, and
    # `assigned_names` sees only bare-name targets, so a state machine written
    # over an attribute was being chained into an `elif` that cannot fire.
    if any(root in _attribute_roots_written(arm) for arm in run):
        return False
    return not all(_exits(arm.body) for arm in run[:-1])


def _attribute_roots_written(scope: ast.AST) -> set[str]:
    """Root names of attribute and subscript stores: `a.b.c = x` -> "a"."""
    found: set[str] = set()
    for node in ast.walk(scope):
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, ast.Delete):
            targets = list(node.targets)
        for target in targets:
            while isinstance(target, (ast.Attribute, ast.Subscript)):
                target = target.value
            if isinstance(target, ast.Name):
                found.add(target.id)
    return found


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

    Not where the chain supplies a default.  Reordering `and`/`or` preserves
    truthiness but not value, and `or` is how Python writes a fallback:

        orders = instance.on_bar(bar) or []
        run_id = manifest.get("run_id") or "baseline"

    Swapping those returns the wrong thing -- `[] or f()` calls `f` every time
    and yields its result, which is neither the intent nor a saving. Two thirds
    of what this rule reported across four real repositories was that idiom,
    recognisable by a literal in the fallback position and a value that escapes
    rather than being tested. A chain that is only ever tested is still fair
    game, literal or not.
    """
    conditions = _condition_slots(ctx.node)
    returned = {id(n.value) for n in ast.walk(ctx.node)
                if isinstance(n, ast.Return) and n.value is not None}
    returns = getattr(ctx.node, "returns", None)
    predicate = isinstance(returns, ast.Name) and returns.id == "bool"
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.BoolOp) or len(node.values) < 2:
            continue
        # Outside a condition the chain is a value, and swapping its operands
        # changes which one comes back: `role = msg.get("role") or role` and
        # `return now().tzinfo or UTC` are fallbacks, and were most of what
        # this rule reported on real code. A `return` stays only where the
        # function declares `-> bool`, so both operands are truth values and
        # the order changes nothing but the cost. Every measured C4.S1 sample
        # is a condition.
        if id(node) not in conditions and (
                id(node) not in returned or not predicate
                or _supplies_a_default(node, ctx.node)):
            continue
        for position, operand in enumerate(node.values[:-1]):
            if not _contains_expensive_call(operand, ctx):
                continue
            # A later operand that reads a name an earlier one binds cannot be
            # promoted past it: `(row := load_row(x)) and row.active` used to be
            # reported, and there `row` does not exist until the call has run.
            bound = _walrus_targets(node.values[: position + 1])
            cheaper = [
                v for v in node.values[position + 1 :]
                if _is_cheap_operand(v, id(node) in conditions)
                and not (ctx.read_names(v) & bound)
            ]
            if not cheaper:
                continue
            yield _evidence(
                unit, "expensive_operand_first", node, ("C4.S1",),
                f"`{ast.unparse(operand)}` calls a function before the cheaper "
                f"test `{ast.unparse(cheaper[0])}`, so short-circuiting cannot "
                f"skip the call; swapping them is only safe if the call has no "
                f"effect the later operand depends on",
                expensive=ast.unparse(operand), cheap=ast.unparse(cheaper[0]),
            )
            break


# Reordering operands is behaviour-preserving only when the promoted operand
# does not depend on the demoted one.  `if initialize() and CONFIG.ready:` is
# the counter-example: promoting `CONFIG.ready` reads it before the call that
# sets it.  Walrus bindings are the one form of that dependency a parser can
# see, and the rule enforces those; everything else is invisible to it, so the
# message names the precondition instead of pretending it was checked.


def _supplies_a_default(node: ast.BoolOp, scope: ast.AST) -> bool:
    """Whether a later operand is a literal standing in as a fallback value.

    `f(x) or []` and `d.get(k) or "baseline"` hand back the literal when the
    call is falsy, so the operands are a value and its default rather than two
    tests, and their order is the whole meaning.
    """
    if any(isinstance(operand, (ast.Constant, ast.List, ast.Dict, ast.Set, ast.Tuple))
           for operand in node.values[1:]):
        return True
    # `fetch_username(post_id) or fallback_user` is the same idiom with the
    # default passed in, and accepting only literals had the rule advising
    # `fallback_user or fetch_username(post_id)`, which never queries at all
    # when the fallback is truthy. A bare *parameter* is the narrow case worth
    # taking: it was handed to this function to be handed back. An attribute --
    # `checksum_changed(m) or config.force` -- reads as a flag and stays a
    # finding, which is as far as syntax can separate the two.
    parameters = {a.arg for a in _all_parameters(scope)}
    return any(isinstance(operand, ast.Name) and operand.id in parameters
               for operand in node.values[1:])


def _is_cheap_operand(node: ast.AST, in_condition: bool) -> bool:
    """Whether promoting this operand ahead of a call is free.

    Anything with no call at all qualifies.  In a condition, so does one built
    only from calls known to cost nothing: `len(data) > 0` and
    `isinstance(x, list)` are the guards this rule exists to promote, and
    banning every call in the second position hid them.

    Predicates only, not conversions.  `sum(int(c) for c in s if c.isdigit()
    and int(c) % 2 == 0)` has `int` on both sides of an `and`, and the call in
    front is what keeps the one behind from raising `ValueError` on a letter --
    the first version of this promoted it and broke the comprehension.

    Only in a condition, though.  Outside one the chain is producing a value,
    and `os.cpu_count() or int(settings.batch_max_workers)` is a fallback whose
    order is its meaning -- letting the conversion call count as "cheap" there
    turned a default into a finding.
    """
    if _scans_a_container(node):
        return False
    calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
    if not calls:
        return True
    return in_condition and all(
        isinstance(c.func, ast.Name) and c.func.id in SAFE_TO_PROMOTE for c in calls
    )


def _scans_a_container(node: ast.AST) -> bool:
    """An `in` test against anything but a literal written out in the source.

    `"```" in text` reads like a cheap test and is a substring search over the
    whole of `text`; `x in rows` walks a list. Only a literal display --
    `x in ("GET", "HEAD")` -- is known to be short.
    """
    literal = (ast.List, ast.Tuple, ast.Set, ast.Dict)
    return any(
        isinstance(op, (ast.In, ast.NotIn)) and not isinstance(right, literal)
        for sub in ast.walk(node) if isinstance(sub, ast.Compare)
        for op, right in zip(sub.ops, sub.comparators)
    )


def _condition_slots(scope: ast.AST) -> set[int]:
    """Expressions evaluated only for their truth, where operand order is free.

    A `BoolOp` nested directly inside another inherits the slot: in
    `if a and (b or c)` the inner chain is still only ever tested.
    """
    found: set[int] = set()
    pending: list[ast.AST] = []
    for node in ast.walk(scope):
        if isinstance(node, (ast.If, ast.While, ast.Assert, ast.IfExp)):
            pending.append(node.test)
        elif isinstance(node, ast.comprehension):
            pending.extend(node.ifs)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            pending.append(node.operand)
    while pending:
        current = pending.pop()
        found.add(id(current))
        if isinstance(current, ast.BoolOp):
            pending.extend(current.values)
    return found


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


def _contains_expensive_call(node: ast.AST, ctx: UnitContext) -> bool:
    """A call that is not one of the recognisably cheap builtins or methods."""
    return any(
        isinstance(sub, ast.Call) and not _is_cheap_call(sub, ctx)
        for sub in ast.walk(node)
    )


def _is_cheap_call(call: ast.Call, ctx: UnitContext) -> bool:
    """A builtin from `CHEAP_CALLS`, or a method from `CHEAP_METHODS`.

    `msg.get("role")`, `name.startswith("v")`, `token[0].isupper()` and
    `math.isfinite(x)` cost about what the comparison beside them costs. What
    C4.S1 measured were calls into the code's own functions -- `_permitted`,
    `_expensive`, `policy.retryable_statuses` -- and treating a dict probe as
    one of those filled the report with reorderings that save nothing.

    `get` on a module is not a dict probe: `requests.get(url)` is a request.
    """
    func = call.func
    if isinstance(func, ast.Name):
        # `max(score, 0.6)` compares two values; `max(scores)` walks a sequence.
        return func.id in CHEAP_CALLS or (func.id in {"min", "max"} and len(call.args) >= 2)
    if isinstance(func, ast.Attribute) and func.attr in CHEAP_METHODS:
        receiver = func.value
        on_module = isinstance(receiver, ast.Name) and receiver.id in ctx.module_aliases
        return not (on_module and func.attr in LOOKUP_METHODS)
    return False


def deep_conditional_nesting(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Branches nested deeply enough that guard clauses would flatten them."""
    deepest, depth = _deepest_if(ctx.node, 0)
    if depth > MAX_NESTING_DEPTH and deepest is not None:
        yield _evidence(
            unit, "deep_conditional_nesting", deepest, ("C4.S3",),
            f"conditionals nested {depth} levels deep; every level re-tests on "
            f"the way to the work at the bottom",
            depth=depth,
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
    """A function that calls itself more than once with no caching of any kind.

    Two self-calls is the *shape* memoization exists for, but the shape alone
    does not make the repair legal, and the rule used to assert what it had not
    checked.  Two conditions are now required.

    First, the subproblems have to actually overlap.  `fib(n-1)` and `fib(n-2)`
    reduce the same value by different amounts, so the same argument recurs all
    over the tree.  These do not:

        merge_sort(l[:half]), merge_sort(l[half:])    disjoint halves
        tree_depth(node.left), tree_depth(node.right) disjoint subtrees

    Every call there gets a slice or a child nothing else will ever be handed,
    so a cache would hold entries it never reads -- and `merge_sort` takes a
    list, which `lru_cache` cannot key on at all.  What separates them is
    whether the calls partition their argument or offset it: a partition splits
    the input, an offset revisits it.

    Second, the caching may already be there.  Checking only for a decorator
    reported eleven already-memoized functions in one sample repository, every
    one of them carrying an explicit `memo` table, which is how memoization is
    usually written when the argument is not hashable or the cache must be
    shared.  A memo table answers *this* advice only: `linear_recursion` is
    about the frame CPython builds per level, which a cache does not remove,
    so it is still reported for a memoized function that recurses once.
    """
    if not isinstance(ctx.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    name = ctx.node.name
    # `self.fib(n - 1)` is the method recursing, and matching only `ast.Name`
    # made the rule blind to every algorithm written as a method -- which is
    # most of them in any class-shaped codebase. But inside a method a bare
    # `fib(n - 1)` is a module-level function that happens to share the name:
    # `def find_port(self): return find_port(self.host)` delegates, and was
    # reported as recursion on every such wrapper.
    is_method = unit.kind == "method"
    self_calls = [
        node for node in ast.walk(ctx.node)
        if isinstance(node, ast.Call) and _calls_itself(node.func, name, is_method)
    ]
    if not self_calls or _has_cache_decorator(ctx.node):
        return
    cached = _has_memo_table(ctx.node)

    # One self-call *inside a loop* is a tree walk: each child is a distinct
    # subproblem, so nothing overlaps and there is nothing to memoise -- and it
    # is not linear recursion either, which is C7.S3's own counter-example
    # (an explicit stack would just reimplement the call stack in Python).
    if len(self_calls) == 1 and ctx.in_loop(self_calls[0]):
        return

    if len(self_calls) >= 2 and not cached and not _partitions_argument(self_calls, ctx.node):
        yield _evidence(
            unit, "recursion_without_memo", self_calls[0], ("C7.S2", "C8.S1"),
            f"`{name}` calls itself {len(self_calls)} times and is not cached, so "
            f"overlapping subproblems are recomputed",
            self_calls=len(self_calls),
        )
    elif len(self_calls) == 1:
        yield _evidence(
            unit, "linear_recursion", self_calls[0], ("C7.S3",),
            f"`{name}` recurses once per call; CPython builds a frame per level "
            f"and does not optimise tail calls",
            self_calls=1,
        )


def _calls_itself(func: ast.AST, name: str, is_method: bool) -> bool:
    """`self.name(...)` in a method, `name(...)` in a function."""
    if isinstance(func, ast.Name):
        return not is_method and func.id == name
    return (is_method and isinstance(func, ast.Attribute) and func.attr == name
            and isinstance(func.value, ast.Name) and func.value.id in {"self", "cls"})


def _partitions_argument(calls: list[ast.Call], scope: ast.AST) -> bool:
    """Whether the self-calls split their argument rather than revisiting it.

    A partition hands each branch a different piece -- a slice, an attribute of
    a node, an element -- and no piece is ever handed to two branches, so there
    is nothing for a cache to hit.  An offset (`n - 1`, `i + 1`, `s[1:]`)
    reduces the same value by different amounts and recurs.
    """
    firsts = [first for first in (_first_argument(call, scope) for call in calls)
              if first is not None]
    if len(firsts) < 2:
        return False
    rendered = {ast.unparse(a) for a in firsts}
    if len(rendered) < len(firsts):
        # The same first argument to every call, with the subproblem carried
        # beside it. Reading only the first argument called that "overlapping
        # by definition" and reported every divide-and-conquer written on
        # indices, but the two cases are distinguishable:
        #
        #   quicksort(arr, low, p - 1) / quicksort(arr, p + 1, high)
        #   count_paths(grid, row - 1, column) / count_paths(grid, row, column - 1)
        #
        # `p` is computed in the body and splits the range at a point neither
        # branch crosses. `row` and `column` are the function's own arguments
        # reduced by a constant, and reducing two of them by turns revisits the
        # same pair from both sides -- which is the whole of dynamic
        # programming. So a pivot partitions and an offset overlaps.
        return _splits_on_a_computed_pivot(calls, scope)
    
    if all(isinstance(a, ast.Attribute) for a in firsts):
        return True  # node.left / node.right: disjoint children
    slices = [a for a in firsts if isinstance(a, ast.Subscript)
              and isinstance(a.slice, ast.Slice)]
    return len(slices) == len(firsts) and _disjoint_slices(slices)


def _first_argument(call: ast.Call, scope: ast.AST) -> ast.AST | None:
    """The value a self-call passes for the function's first parameter.

    `walk(node.left, depth + 1)` and `walk(node=node.left, depth=depth + 1)` are
    the same recursion, and reading `call.args[0]` saw only the first. With no
    positional arguments to read, every keyword-written tree walk looked like it
    revisited its argument, and the rule offered a cache for a traversal with no
    overlapping subproblems.
    """
    if call.args:
        return call.args[0]
    parameters = [a.arg for a in _all_parameters(scope)]
    first = next((p for p in parameters if p != "self"), None)
    if first is None:
        return None
    return next((k.value for k in call.keywords if k.arg == first), None)


def _splits_on_a_computed_pivot(calls: list[ast.Call], scope: ast.AST) -> bool:
    """Whether the recursive arguments are cut at a value the body computed.

    A pivot -- `p = partition(arr, low, high)` -- exists only inside one frame,
    so the ranges either side of it are handed to one branch each and never
    meet.  An argument built only from the function's own parameters and
    constants is an offset of what this frame was given, and the branches
    converge.
    """
    parameters = {a.arg for a in _all_parameters(scope)}
    locals_ = {
        target.id
        for node in ast.walk(scope) if isinstance(node, ast.Assign)
        for t in node.targets for target in ast.walk(t)
        if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store)
    } - parameters
    return any(
        name in locals_
        for call in calls for argument in call.args
        for node in ast.walk(argument)
        if isinstance(node, ast.Name) for name in (node.id,)
    )


def _all_parameters(scope: ast.AST) -> list[ast.arg]:
    arguments = getattr(scope, "args", None)
    if arguments is None:
        return []
    return [*getattr(arguments, "posonlyargs", []), *arguments.args,
            *arguments.kwonlyargs,
            *([arguments.vararg] if arguments.vararg else []),
            *([arguments.kwarg] if arguments.kwarg else [])]


def _disjoint_slices(slices: list[ast.Subscript]) -> bool:
    """Whether a set of slices cuts its sequence into non-overlapping pieces.

    `l[:half]` and `l[half:]` meet at one bound and share nothing.  `s1[1:]`
    twice is the same piece, and `nested[0]` beside `nested[1:]` still leaves
    the tail shared with a later call, so only the clean split counts.
    """
    if len(slices) != 2:
        return False
    first, second = (ast.unparse(s.slice) for s in slices)
    if not first.startswith(":") or not second.endswith(":"):
        first, second = second, first
    return (
        first.startswith(":") and second.endswith(":")
        and first[1:] == second[:-1] and first[1:] != ""
    )


MEMO_TABLE_NAMES = frozenset({"memo", "cache", "seen", "known", "table", "lookup",
                              "memoized", "_cache", "_memo", "dp"})


def _has_memo_table(node: ast.AST) -> bool:
    """Whether the function already caches results in a table it manages itself.

    The shape is a mapping that is both read as a membership test or `.get()`
    and written by subscript assignment -- `if n in memo: return memo[n]` with
    `memo[n] = ...` further down.  That is memoization; the decorator is just
    the tidier spelling of it.
    """
    names = {
        target.value.id
        for target in ast.walk(node)
        if isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Name)
        and isinstance(target.ctx, ast.Store)
    }
    if not names:
        return False
    for candidate in names:
        if candidate not in MEMO_TABLE_NAMES and not any(
            hint in candidate.lower() for hint in ("memo", "cache", "dp", "seen")
        ):
            continue
        for probe in ast.walk(node):
            if (
                isinstance(probe, ast.Compare)
                and any(isinstance(op, (ast.In, ast.NotIn)) for op in probe.ops)
                and any(isinstance(c, ast.Name) and c.id == candidate
                        for c in probe.comparators)
            ):
                return True
            if (
                isinstance(probe, ast.Call)
                and isinstance(probe.func, ast.Attribute)
                and probe.func.attr == "get"
                and isinstance(probe.func.value, ast.Name)
                and probe.func.value.id == candidate
            ):
                return True
    return False


def _has_cache_decorator(node: ast.AST) -> bool:
    names = {
        ast.unparse(d).split("(")[0].split(".")[-1]
        for d in getattr(node, "decorator_list", [])
    }
    return bool(names & {"cache", "lru_cache", "cached_property", "memoize"})


def repeated_pure_call(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """The same pure call appearing more than once outside any loop.

    Inside anything that repeats this is C3.S2 and the loop analyzer owns it, so
    this rule deliberately looks only at straight-line code (C1.S4).

    "Repeats" is `ctx.repeats`, not `ctx.in_loop`.  `in_loop` sees `for` and
    `while` and not comprehensions, so the same call written three times in a
    comprehension used to arrive here and be reported as straight-line
    redundancy "with nothing changing in between" -- which is the wrong
    subcategory for work that runs once per element, and the wrong advice,
    since there is no straight line to hoist it into.

    Calls inside a nested `def` are not counted either.  One occurrence in the
    body plus two in a closure is not the same expression computed three times
    in one scope; the closure's two run whenever it is called.

    Two things disqualify a repeat.  A call that writes somewhere -- `print`,
    a logger -- is not a value to compute once and reuse; the second call is
    the point of it.  And occurrences in different `except` handlers or
    different arms of an `if` never both run, so there is no repeated work to
    remove: `print(e)` in three handlers was this rule's commonest report on
    real code and none of it was a finding.
    """
    seen: dict[str, list[ast.Call]] = {}
    header = _header_nodes(ctx.node)
    for node in ctx.own_nodes():
        if not isinstance(node, ast.Call) or ctx.repeats(node):
            continue
        if id(node) in header:
            continue
        parent = ctx.parent_of(node)
        if isinstance(parent, ast.Await):
            parent = ctx.parent_of(parent)
        if isinstance(parent, ast.Expr):
            continue  # result dropped: it runs for what it does, not what it returns
        if isinstance(parent, ast.withitem) or _inside_raise(node, ctx):
            # `with suppress(OSError):` and `raise Corrupt("...")` need an
            # object of their own each time, and only one raise ever runs.
            continue
        if not node.args or not _repeatable(node, ctx):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in TRIVIAL_CALLS:
            continue  # recomputing len(x) twice is not worth a claim
        if is_cheap_expression(node):
            continue  # nor is `max(n_total, 1)`: one builtin call on scalars
        if _writes_somewhere(node.func):
            continue
        seen.setdefault(ast.unparse(node), []).append(node)

    branches = _exclusive_branches(ctx.node)
    for expression, calls in seen.items():
        if len(calls) < MIN_REPEATED_CALLS:
            continue
        reachable = [_branch_of(call, branches) for call in calls]
        owners = {slot[0] for slot in reachable if slot is not None}
        if (None not in reachable and len(owners) == 1
                and len(set(reachable)) == len(calls)):
            continue  # one arm each of the same statement: never both run
        yield _evidence(
            unit, "repeated_pure_call", calls[0], ("C1.S4",),
            f"`{expression}` is computed {len(calls)} times in the same scope; "
            f"if nothing it reads changes in between, once is enough",
            expression=expression, occurrences=len(calls),
        )


def _inside_raise(node: ast.AST, ctx: UnitContext) -> bool:
    current = ctx.parent_of(node)
    while current is not None and not isinstance(current, ast.stmt):
        current = ctx.parent_of(current)
    return isinstance(current, ast.Raise)


def _header_nodes(function: ast.AST) -> set[int]:
    """Nodes in a definition's decorators, defaults and annotations.

    They run once, when the `def` itself runs, in the scope around it --
    `def start(a=Option(False), b=Option(False), c=Option(False))` is three
    separate default objects, each of which has to exist, not one call
    computed three times.
    """
    if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return set()
    arguments = function.args
    roots: list[ast.AST] = [*arguments.defaults,
                            *(d for d in arguments.kw_defaults if d is not None)]
    if not isinstance(function, ast.Lambda):
        roots += function.decorator_list
        if function.returns is not None:
            roots.append(function.returns)
        every = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs,
                 *(a for a in (arguments.vararg, arguments.kwarg) if a is not None)]
        roots += [a.annotation for a in every if a.annotation is not None]
    return {id(sub) for root in roots for sub in ast.walk(root)}


WRITING_CALLS = frozenset({"print", "write", "log", "debug", "info", "warning",
                           "warn", "error", "exception", "critical"})


def _writes_somewhere(func: ast.AST) -> bool:
    """Whether the call's only purpose is the side effect it performs."""
    name = func.id if isinstance(func, ast.Name) else (
        func.attr if isinstance(func, ast.Attribute) else None)
    return name in WRITING_CALLS


def _exclusive_branches(scope: ast.AST) -> dict[int, int]:
    """Map each node to the mutually exclusive arm it sits in, if any.

    `except` handlers of one `try`, and the arms of an `if`, are alternatives:
    at most one runs, so the same call appearing in several of them is written
    once per case rather than computed repeatedly.

    Which `if` they belong to is half the answer, and used to be discarded. A
    running counter gave three consecutive `if` statements three different arm
    numbers, so `parse(data)` in each of them looked like three alternatives
    when all three can run in sequence -- the exact shape the rule exists for.
    The owner is recorded beside the arm now, and only arms of the *same*
    statement exclude each other.
    """
    owner: dict[int, tuple[int, int]] = {}
    for node in ast.walk(scope):
        arms: list[list[ast.stmt]] = []
        if isinstance(node, ast.Try):
            arms = [h.body for h in node.handlers]
        elif isinstance(node, ast.If):
            arms = [node.body, node.orelse]
        for index, body in enumerate(arms):
            for statement in body:
                for inner in ast.walk(statement):
                    owner.setdefault(id(inner), (id(node), index))
    return owner


def _branch_of(node: ast.AST, branches: dict[int, int]):
    return branches.get(id(node))


def _repeatable(call: ast.Call, ctx: UnitContext) -> bool:
    """Whether recomputing this call is plausibly redundant rather than required.

    `is_pure` only trusts builtins and known-safe methods, and gating on it
    alone made this rule almost unreachable: `parse_manifest(path)` three times
    in one function -- exactly what C1.S4 is about -- is a call to a plain
    function, which nothing can prove pure.  So a bare-name call with arguments
    counts, and the message asks the reader to confirm it has no side effect.

    Method calls stay restricted to the recognised-pure set.  `session.get(k)`
    repeated three times is a real finding and it is C8.S4, not this one.

    Bare names that are famously *not* pure are excluded by name, because the
    advice for them is destructive rather than merely unhelpful: told that
    `randint(1, 6)` is "computed 3 times with nothing changing in between", a
    reader who caches it turns three dice into one.  The same goes for
    `next(stream)`, `time()` and `input()`.  A blocklist is not a proof of
    purity for everything else -- the message still asks the reader to confirm
    -- but it keeps the rule from recommending a bug.
    """
    if ctx.is_pure(call):
        return True
    if isinstance(call.func, ast.Name) and call.func.id in NONDETERMINISTIC_CALLS:
        return False
    return isinstance(call.func, ast.Name) and all(
        isinstance(argument, (ast.Name, ast.Constant, ast.Attribute))
        for argument in call.args
    ) and not call.keywords


def manual_builtin_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A loop hand-rolling `max`, `min` or `sum` over its iterable."""
    non_numeric = _non_numeric_accumulators(ctx.node)
    for loop in ctx.loops:
        # The tracking has to be the whole body. A loop that also records every
        # prefix maximum computes a running series, and no single `max()` call
        # replaces it -- reporting one was telling the reader to delete output.
        if not isinstance(loop, ast.For) or len(loop.body) != 1:
            continue
        for node in loop.body:
            builtin = _hand_rolled_builtin(node, non_numeric)
            if builtin is None:
                continue
            yield _evidence(
                unit, "manual_builtin_loop", loop, ("C10.S1",),
                f"the loop maintains {BUILTIN_EQUIVALENTS[builtin]} by hand; "
                f"`{builtin}()` does this in C",
                builtin=builtin,
            )
            break


def _hand_rolled_builtin(node: ast.AST, non_numeric: set[str]) -> str | None:
    """Detect `if x > best: best = x` and `total += x` loop bodies.

    The `None`-guarded form counts too.  Starting an extreme at `None` and
    writing `if best is None or x < best:` is at least as common as seeding it
    from the first element, and requiring a bare comparison missed all of it.
    The repair there needs `min(..., default=None)` to keep the empty case.

    A *filtered* sum counts as well:

        for n in lst:
            if n % 2 == 0:
                total += n          ->  sum(n for n in lst if n % 2 == 0)

    The guarded extreme was already reported and the guarded sum was not, which
    was an accident of shape rather than a judgement -- `if` around an
    `AugAssign` reads as a comprehension filter exactly as `if` around an
    `Assign` reads as a comparison.  A guarded *counter* (`found += 1`) is not
    the same thing and stays out; see below.
    """
    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
        return _running_sum(node, non_numeric)
    if not isinstance(node, ast.If) or len(node.body) != 1 or node.orelse:
        return None
    inner = node.body[0]
    if isinstance(inner, ast.AugAssign) and isinstance(inner.op, ast.Add):
        if _running_sum(inner, non_numeric) is None:
            return None
        # `total += n` is a filtered sum and `sum()` does the adding in C.
        return "sum"
    if not isinstance(inner, ast.Assign):
        return None
    # The assignment has to be the one the comparison licenses. Reading the
    # operator and nothing else made `if s > limit: alert = True` a running
    # maximum, and every flag, counter and log trigger written inside an
    # `if x > y:` with it. `max` keeps the larger operand; it does not set a
    # flag.
    if not _updates_the_compared_value(node.test, inner):
        return None
    return _extreme_from(node.test)


def _running_sum(node: ast.AugAssign, non_numeric: set[str]) -> str | None:
    """Whether `x += v` accumulates one total that `sum()` could produce.

    Two things disqualify it, and the unguarded path used to check neither.

    The target has to be a single name.  `freqs[word] += 1` writes a different
    slot every pass -- a histogram, whose repair is `Counter`, not `sum` -- and
    reading the target as an accumulator reported three of them on the
    evaluation corpus plus `H[i % len(H)] += 1`, where `sum()` cannot express
    the result at all.

    And the value cannot be a constant.  `count += 1` is a counter: `sum(1 for
    ...)` hands the work back to a generator frame per element with no C loop to
    win it back, which is exactly why the guarded path below already refused
    it. The repair a counter wants is `len()`, and this rule does not name it.
    """
    name = _target_name_of(node.target)
    if name is None or name in non_numeric:
        return None
    return None if isinstance(node.value, ast.Constant) else "sum"


def _target_name_of(node: ast.AST) -> str | None:
    return node.id if isinstance(node, ast.Name) else None


def _non_numeric_accumulators(scope: ast.AST) -> set[str]:
    """Names seeded with something `sum()` cannot add.

    `out = ""` then `out += msg` is not a hand-rolled `sum`: `sum` of strings
    raises `TypeError: sum() can't sum strings [use ''.join(seq) instead]`, and
    `sum(batches, [])` is the quadratic concatenation C10.S4 exists to warn
    about. As with `string_concat_in_loop`, what the accumulator *is* is
    decided by where it starts, not by what gets added to it.
    """
    found: set[str] = set()
    for node in ast.walk(scope):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not isinstance(target, ast.Name):
            continue
        textual = isinstance(value, ast.Constant) and isinstance(value.value, (str, bytes))
        sequence = isinstance(value, (ast.List, ast.Dict, ast.Set, ast.Tuple,
                                      ast.ListComp, ast.DictComp, ast.SetComp))
        if textual or sequence:
            found.add(target.id)
    return found


def _updates_the_compared_value(test: ast.AST, assign: ast.Assign) -> bool:
    """Whether `assign` stores one side of `test` into the other.

    `if x > best: best = x` keeps the larger of the two, which is `max`.
    `if s > limit: alert = True` shares the shape and means nothing like it.
    """
    if isinstance(test, ast.BoolOp):
        return any(_updates_the_compared_value(v, assign) for v in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(assign.targets) != 1:
        return False
    operands = {ast.unparse(test.left), ast.unparse(test.comparators[0])}
    # `best, best_score = record, record.score` tracks the element beside the
    # value, so the pair that matters is one of several. Any pair storing one
    # compared operand into the other is the extreme being kept.
    return any(ast.unparse(target) in operands and ast.unparse(value) in operands
               for target, value in _assigned_pairs(assign))


def _assigned_pairs(assign: ast.Assign):
    """`(target, value)` pairs, unpacking `a, b = x, y` into two of them."""
    target, value = assign.targets[0], assign.value
    if (isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple)
            and len(target.elts) == len(value.elts)):
        return list(zip(target.elts, value.elts))
    return [(target, value)]


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


TEST_BASES = frozenset({"TestCase", "IsolatedAsyncioTestCase", "TransactionTestCase"})
"""Framework bases whose methods are found by name and called by the runner."""


def _uses_implicit_super(node: ast.AST) -> bool:
    """Whether the body calls zero-argument `super()`.

    `super()` with no arguments compiles to a lookup using `__class__` and the
    method's first positional parameter, so it works only in a method that has
    one. Making such a method static does not merely change a lookup -- it
    raises `RuntimeError: super(): no arguments`. The body never names `self`,
    so the rule saw an unused parameter and suggested the one change that
    breaks it.
    """
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "super" and not n.args
               for n in ast.walk(node))


def _is_test_method(unit: UnitRef, ctx: UnitContext) -> bool:
    """Whether this is a test the framework discovers rather than code we call.

    A runner collects `test_*` methods off an instance; nothing in the project
    calls them by name. The repair this rule names is to make the method static
    *and rewrite its call sites* as `Class.method(...)`, and there are no call
    sites here, so the finding asks for a change with nothing on the other side
    of it. Matching the name rather than the base class is deliberate: the base
    may be `unittest.TestCase`, a project mixin, or nothing at all under
    pytest, and the naming convention is the part all of them share.
    """
    return ctx.node.name.startswith("test_") and unit.kind == "method"


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
    if _uses_implicit_super(ctx.node):
        return
    if _is_test_method(unit, ctx):
        return
    # A method that ignores `self` and is also overridden -- or is itself an
    # override -- is the dispatch point. The decorator alone would be harmless,
    # but the repair that pays for it changes the call site to `Class.method(...)`,
    # and that skips every override.
    if ctx.node.name in ctx.overridden_methods:
        return
    yield _evidence(
        unit, "method_ignores_self", ctx.node, ("C2.S2",),
        f"`{ctx.node.name}` never uses `self`, so every call builds a bound "
        f"method object for nothing",
        method=ctx.node.name,
    )


def trivial_delegation(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A function whose entire body forwards its own arguments to one call.

    Restricted to *pure* forwarding -- same arguments, in the same order, with
    nothing added.  Anything looser fires on most of a library's public API,
    where a thin named wrapper is deliberate design rather than waste.  Even
    so it only costs energy on a hot path, which the reader has to check.

    The receiver of an attribute call is an argument too.  `self._backend.count()`
    forwards, because `self` is the function's own first parameter and the call
    adds nothing the caller did not already have.  `"".join(strings)` does not:
    the separator is a choice the wrapper makes, so the wrapper has behaviour of
    its own and deleting it changes what the caller must write.

    A call made directly on `self` is left alone, because `self_delegation_chain`
    reports exactly that shape and names C2.S3 as well as C2.S1.  Both rules
    fired on it, so one fact arrived as two findings with two signals and two
    root causes -- and both of those are terms in a unit's ranking.  Eight of
    the twenty-one delegation findings on the evaluation corpus were one fact
    counted twice.
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
    if not _receiver_is_free(value.func, ctx.node):
        return
    if (isinstance(value.func, ast.Attribute) and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "self"):
        return  # `self_delegation_chain` owns this shape; see the docstring
    yield _evidence(
        unit, "trivial_delegation", ctx.node, ("C2.S1",),
        f"`{ctx.node.name}` only forwards to `{ast.unparse(value.func)}`, adding "
        f"a stack frame per call without adding behaviour",
        delegate=ast.unparse(value.func),
    )


def _receiver_is_free(func: ast.AST, function: ast.AST) -> bool:
    """Whether an attribute call's receiver is something the caller already holds.

    A receiver built out of a literal or an expression is part of what the
    wrapper does, not something it forwards.
    """
    if not isinstance(func, ast.Attribute):
        return True
    base = func.value
    while isinstance(base, ast.Attribute):
        base = base.value
    return isinstance(base, ast.Name) and (
        base.id == "self" or base.id in _parameter_names(function)
    )


def _parameter_names(function: ast.AST) -> set[str]:
    arguments = getattr(function, "args", None)
    if arguments is None:
        return set()
    return {
        a.arg for a in (
            *getattr(arguments, "posonlyargs", []),
            *arguments.args,
            *arguments.kwonlyargs,
        )
    }


def _forwards_arguments(function: ast.AST, call: ast.Call) -> bool:
    """Whether `call` passes exactly the function's own parameters, in order.

    A parameterless wrapper counts.  `def count(self): return
    self._backend.count()` is as pure a forward as one that passes arguments,
    and requiring at least one parameter dropped the whole family.

    So does the `*args, **kwargs` proxy, which is how forwarding is written
    whenever the signature is not being restated -- and which the strict
    positional match could never see, since `*args` unparses to a `Starred`
    and `**kwargs` lands in `call.keywords` with no name at all.
    """
    if _forwards_star_args(function, call):
        return True
    if call.keywords:
        return False
    parameters = [a.arg for a in function.args.args if a.arg != "self"]
    passed = [a.id for a in call.args if isinstance(a, ast.Name)]
    return len(passed) == len(call.args) and passed == parameters


def _forwards_star_args(function: ast.AST, call: ast.Call) -> bool:
    """`f(*args, **kwargs)` where `args`/`kwargs` are this function's own."""
    arguments = function.args
    vararg = arguments.vararg.arg if arguments.vararg else None
    kwarg = arguments.kwarg.arg if arguments.kwarg else None
    if vararg is None and kwarg is None:
        return False
    starred = [a for a in call.args if isinstance(a, ast.Starred)]
    if len(starred) != len(call.args) or len(starred) > 1:
        return False
    if starred and not (isinstance(starred[0].value, ast.Name)
                        and starred[0].value.id == vararg):
        return False
    doubled = [k for k in call.keywords if k.arg is None]
    if len(doubled) != len(call.keywords) or len(doubled) > 1:
        return False
    if doubled and not (isinstance(doubled[0].value, ast.Name)
                        and doubled[0].value.id == kwarg):
        return False
    named = [a.arg for a in arguments.args if a.arg != "self"]
    return not named and bool(starred or doubled)


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
        if not isinstance(node, ast.Call):
            continue
        if _dispatched_concurrently(node, ctx):
            continue
        if _streams_or_retries(node, ctx):
            continue
        if isinstance(node.func, ast.Name):
            # `from urllib.request import urlopen` binds the function itself,
            # and a rule matching only `ast.Attribute` never saw it.
            if node.func.id not in UNAMBIGUOUS_IO_CALLS:
                continue
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
            if name not in UNAMBIGUOUS_IO_CALLS and not (
                name in AMBIGUOUS_IO_CALLS | DATABASE_CALLS
                and _is_io_receiver(node.func.value, ctx)
            ):
                continue
        else:
            continue
        yield _evidence(
            unit, "io_call_in_loop", node, ("C9.S1", "C9.S3"),
            f"`{ast.unparse(node.func)}()` looks like it leaves the process, and "
            f"it runs once per iteration; batching would amortise the round trip",
            call=name,
            loop_line=getattr(ctx.repeats_around(node)[-1], "lineno", unit.lineno),
        )


def _streams_or_retries(call: ast.Call, ctx: UnitContext) -> bool:
    """Whether the loop around `call` is already the right shape for it.

    Two loops repeat an I/O call on purpose, and batching fits neither:

        while chunk := handle.read(65536):     streaming: the read is the loop's
            digest.update(chunk)               own condition, already chunked

        for attempt in range(retries):         a retry: the `try` that holds the
            try:                               call leaves the loop on success,
                return session.post(url)       so it runs once when it works
            except TransientError: ...
    """
    loops = [s for s in ctx.repeats_around(call) if isinstance(s, LOOP_NODES)]
    if not loops:
        return False
    loop = loops[-1]
    current, parent = call, ctx.parent_of(call)
    while parent is not None and current is not loop:
        if isinstance(parent, ast.While) and current is parent.test:
            return True
        if (isinstance(parent, ast.Try) and any(current is s for s in parent.body)
                and any(isinstance(n, (ast.Return, ast.Break))
                        for s in (*parent.body, *parent.orelse)
                        for n in _walk_same_loop(s))):
            return True
        current, parent = parent, ctx.parent_of(parent)
    return False


def _walk_same_loop(node: ast.AST):
    """Walk `node` without entering nested loops or definitions."""
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, LOOP_NODES + OPAQUE_NODES + (ast.Lambda,)):
            continue
        yield from _walk_same_loop(child)


CONCURRENT_DISPATCH = frozenset({
    "gather", "wait", "as_completed", "create_task", "ensure_future",
    "map", "starmap", "imap", "imap_unordered", "submit",
})
"""Runners that start work before waiting for it.

`asyncio.wait_for` is deliberately absent: it awaits *one* awaitable with a
deadline, so `wait_for(session.get(item), timeout=1)` in a loop is as
sequential as the bare call, and listing it let a timeout silence the rule."""


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
    if _bound_to_something_in_memory(node.id, ctx):
        return False
    if node.id.lower().lstrip("_") in IO_RECEIVERS:
        return True
    origin = ctx.imports.get(node.id, "")
    return origin.split(".")[0] in IO_MODULES


IN_MEMORY_FACTORIES = frozenset({
    "StringIO", "BytesIO", "Queue", "LifoQueue", "PriorityQueue", "SimpleQueue",
    "deque", "defaultdict", "Counter", "OrderedDict", "list", "dict", "set",
})
"""Constructors whose result never leaves the process.

`IO_RECEIVERS` matches on the *name* of the receiver, which is what makes the
rule work at all -- there is no type information to match on -- and it is also
what makes it wrong when the name is honest about the role and silent about the
medium.  `stream`, `handle`, `pool`, `writer` and `file` are all in that set,
and all of them are ordinary names for an in-memory object:

    stream = io.StringIO()
    for row in rows:
        stream.write(row.text)     # reported as leaving the process

    pool = queue.Queue()
    for item in items:
        pool.get()                 # same

Neither is I/O and neither is C9.S1, which is about unbatched round trips.  A
binding visible in the unit settles it, so when there is one, it wins over the
name.
"""


def _bound_to_something_in_memory(name: str, ctx: UnitContext) -> bool:
    """Whether the unit binds `name` from a constructor that stays in memory.

    Only a binding this unit can see counts.  A parameter or an attribute is
    left to the name heuristic, because nothing here can tell what was passed
    in -- which is the right way round: this narrows a name match that would
    otherwise be wrong, and never widens one.
    """
    for node in ctx.own_nodes():
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            continue
        func = node.value.func
        built = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if built in IN_MEMORY_FACTORIES:
            return True
    return False


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
        )


LOCK_WORDS = frozenset({"lock", "rlock", "semaphore", "mutex", "monitor", "latch"})


def _looks_like_lock(node: ast.AST) -> bool:
    """Whether an expression names a synchronisation primitive.

    Matched on whole words rather than as a substring. `"lock" in text` is true
    of `memory_block`, `system_clock`, `unlocked_view` and `interlock`, so
    `with memory_block:` in a loop was reported as lock contention.
    """
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|[0-9]+",
                       ast.unparse(node))
    return any(word.lower() in LOCK_WORDS for word in words)


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
