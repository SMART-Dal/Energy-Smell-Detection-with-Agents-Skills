"""Analyzers for root causes the first three modules left uncovered.

`loops.py`, `memory.py` and `structure.py` grew around the patterns that are
easy to see: something expensive, inside a loop.  That left 27 of the 65 root
causes with no static rule at all, which is a problem for the tool and a worse
one for the experiment -- a root cause the scanner can never mention is one the
agent will only find in the arms where it goes looking on its own.

The rules here close as much of that gap as syntax allows.  Several exist
because one of Javad's 92 sample pairs is exactly that pattern and measured as a
real saving, which is a better reason to write an analyzer than a hunch:

    MultiplyByFactor        i * 3.0 vs i * 3        -> float_literal_on_int_data
    AssignType              list vs tuple constant  -> constant_sequence_literal
    SumTopK                 sorted(xs)[:k]          -> sort_then_slice

What still has no rule after this file is honest to leave alone: C12 needs
memory layout, C11.S5 needs to know which calls are independent, C5.S2 and
C6.S4 need to know what the data is for.  Those are read by hand, and
`reference/README.md` tells the agent so.
"""

from __future__ import annotations

import ast
from typing import Iterator

from ..models import Evidence, Strength, UnitRef
from ..context import LOOP_NODES, PURE_BUILTINS, PURE_METHODS, UnitContext

# Calls whose whole purpose is to duplicate a container.
COPY_CALLS = frozenset({"list", "dict", "set", "copy", "deepcopy", "tuple"})

# Interpreter housekeeping: correct to call, ruinous to call repeatedly.
RUNTIME_MANAGEMENT = {
    ("gc", "collect"), ("gc", "enable"), ("gc", "disable"),
    ("sys", "setrecursionlimit"), ("sys", "settrace"), ("sys", "setprofile"),
    ("importlib", "reload"), ("locale", "setlocale"),
}

# Blocking calls that stall an event loop when awaited from `async def`.
BLOCKING_IN_ASYNC = {
    ("time", "sleep"), ("requests", "get"), ("requests", "post"),
    ("requests", "put"), ("requests", "delete"), ("subprocess", "run"),
    ("subprocess", "call"), ("subprocess", "check_output"), ("os", "system"),
    ("socket", "recv"), ("urllib", "urlopen"),
}

# Comparisons that build a whole new object just to answer a yes/no question.
EXPENSIVE_COMPARISON_CALLS = frozenset({"sorted", "str", "repr", "list", "set", "tuple"})

MIN_USES_TO_HOIST = 3
"""Reads of one global inside a loop before hoisting it is worth mentioning."""

MAX_HOISTS_PER_LOOP = 2
"""How many names one loop may be reported for, worst first."""


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


def _dotted(func: ast.AST) -> tuple[str, str] | None:
    """`re.compile` -> ("re", "compile"); anything else -> None."""
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return (func.value.id, func.attr)
    return None


def _runs_every_iteration(ctx: UnitContext, node: ast.AST) -> bool:
    """Whether `node` is re-evaluated on each pass of the loop that encloses it.

    `ctx.in_loop` says only that a loop is somewhere above the node, and a
    `for` loop's own iterable sits inside the loop by that measure while being
    evaluated exactly once.  Anything that says "on every iteration" has to ask
    this instead, or it will report `for key in list(cache)` as a per-iteration
    copy when the copy is taken once, before the first pass.
    """
    loops = ctx.loops_around(node)
    if not loops:
        return False
    innermost = loops[-1]
    if isinstance(innermost, (ast.For, ast.AsyncFor)):
        iterable = {id(n) for n in ast.walk(innermost.iter)}
        if id(node) in iterable:
            return len(loops) > 1
    return True


# -- C5.S3  over-provisioned data type -------------------------------------


def float_literal_on_int_data(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A float constant in arithmetic that would otherwise stay integer.

        [i * 3.0 for i in lst]      every product is a float
        [i * 3   for i in lst]      every product stays an int

    Python integers in the small range are cached and their arithmetic avoids
    the float boxing path entirely, so the `.0` costs an allocation per element
    for a value nobody asked to be fractional.  Only reported inside a loop or
    comprehension: one float multiplication is nothing.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.BinOp) or not ctx.in_loop(node):
            continue
        if not isinstance(node.op, (ast.Mult, ast.Add, ast.Sub)):
            continue
        for operand in (node.left, node.right):
            if (
                isinstance(operand, ast.Constant)
                and isinstance(operand.value, float)
                and operand.value.is_integer()
            ):
                yield _evidence(
                    unit, "float_literal_on_int_data", node, ("C5.S3",),
                    f"`{ast.unparse(node)}` forces a float result with the literal "
                    f"`{operand.value}`, which has no fractional part; every "
                    f"element pays for a float allocation the value does not need",
                    literal=operand.value,
                    strength=Strength.CONTEXTUAL,
                )
                break


def constant_sequence_literal(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A list literal of constants that is only ever read.

        types = ["red", "blue", "green"]     rebuilt element by element
        types = ("red", "blue", "green")     loaded as one constant

    CPython stores a constant tuple in the code object and pushes it whole; a
    list literal is built with a BUILD_LIST and one store per element on every
    call.  The rewrite is only safe when nothing mutates the binding, which is
    what the assigned-names check below is for.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target, value = node.targets[0], node.value
        if not isinstance(target, ast.Name) or not isinstance(value, ast.List):
            continue
        if not value.elts or not all(isinstance(e, ast.Constant) for e in value.elts):
            continue
        if _is_mutated(ctx.node, target.id):
            continue
        yield _evidence(
            unit, "constant_sequence_literal", node, ("C5.S3", "C6.S1"),
            f"`{target.id}` is a list of {len(value.elts)} constants that is never "
            f"mutated; a tuple literal is stored whole in the code object instead "
            f"of being rebuilt element by element on every call",
            name=target.id,
            size=len(value.elts),
            strength=Strength.LIKELY if ctx.in_loop(node) else Strength.CONTEXTUAL,
        )


def _is_mutated(scope: ast.AST, name: str) -> bool:
    """Whether `name` is ever appended to, assigned into, or reassigned."""
    for node in ast.walk(scope):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id == name:
                if node.func.attr in {"append", "extend", "insert", "remove", "pop",
                                      "sort", "reverse", "clear"}:
                    return True
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id == name and isinstance(node.ctx, (ast.Store, ast.Del)):
                return True
    return False


# -- C10.S5  inefficient scope lookup --------------------------------------


def global_lookup_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A name resolved through the global or builtin scope on every iteration.

    A local name is an array index into the frame; a global is a dict lookup in
    the module namespace, and a builtin is that lookup plus a second one in
    `builtins`.  Inside a hot loop the difference is paid per iteration, and
    binding the name once above the loop removes it.

    Only names the unit never assigns are reported, since an assigned name is
    already local.

    The threshold below matters more than the rule. Reporting every non-local
    name read in a loop produced 45 hits across `requests` -- more than every
    other analyzer combined, and mostly imported helpers read once per
    iteration, where a hoist saves one dict lookup against the cost of a
    clearer name. Only a name read at least MIN_USES times per iteration is
    worth binding, and only the worst two per loop are reported.
    """
    local = ctx.assigned_names(ctx.node) | _parameter_names(ctx.node)
    for loop in ctx.loops:
        counts: dict[str, int] = {}
        first: dict[str, ast.AST] = {}
        for node in ast.walk(loop):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id in local or ctx.loop_depth(node) < 1:
                    continue
                counts[node.id] = counts.get(node.id, 0) + 1
                first.setdefault(node.id, node)

        worst = sorted(counts.items(), key=lambda pair: -pair[1])[:MAX_HOISTS_PER_LOOP]
        for name, uses in worst:
            if uses < MIN_USES_TO_HOIST:
                continue
            yield _evidence(
                unit, "global_lookup_in_loop", first[name], ("C10.S5",),
                f"`{name}` is not local to this unit and is read {uses} times inside "
                f"the loop, so each read costs a namespace dict lookup; binding it "
                f"to a local above the loop turns those into frame slot reads",
                name=name,
                uses=uses,
                loop_line=loop.lineno,
                strength=Strength.CONTEXTUAL,
            )


def _parameter_names(node: ast.AST) -> set[str]:
    arguments = getattr(node, "args", None)
    if not isinstance(arguments, ast.arguments):
        return set()
    every = [
        *arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs,
        *([arguments.vararg] if arguments.vararg else []),
        *([arguments.kwarg] if arguments.kwarg else []),
    ]
    return {a.arg for a in every}


# -- C6.S2  unnecessary copying --------------------------------------------


def copy_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A container duplicated inside a loop.

        for row in rows:
            current = list(defaults)     a fresh copy every iteration
            current.update(row)

    Sometimes required -- the copy is mutated and must not be shared. Reported
    as `contextual` for that reason: the fact is certain, the fault is not.
    """
    for node in ast.walk(ctx.node):
        if not ctx.in_loop(node):
            continue
        described = None
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else None
            dotted = _dotted(node.func)
            if dotted and dotted[1] in {"copy", "deepcopy"}:
                described = f"{dotted[0]}.{dotted[1]}()"
            elif name in COPY_CALLS and len(node.args) == 1:
                if isinstance(node.args[0], (ast.Name, ast.Attribute)):
                    described = f"{name}()"
        elif isinstance(node, ast.Subscript) and _is_full_slice(node.slice):
            described = "a `[:]` slice"

        if described:
            yield _evidence(
                unit, "copy_in_loop", node, ("C6.S2",),
                f"`{ast.unparse(node)}` duplicates a container on every iteration "
                f"using {described}; the copy is only needed if something mutates "
                f"it and the original must not change",
                strength=Strength.CONTEXTUAL,
            )


def _is_full_slice(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Slice)
        and node.lower is None and node.upper is None and node.step is None
    )


# -- C7.S4  inefficient operation ordering ---------------------------------


def sort_then_slice(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A full sort whose result is immediately truncated.

        sum(sorted(lst)[:k])            sorts all n elements
        sum(heapq.nsmallest(k, lst))    keeps a heap of k

    n log n against n log k, which for k much smaller than n is most of the
    work thrown away. Also fires on `sorted(...)[0]` and `[-1]`, where the
    answer is `min` or `max`.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Subscript):
            continue
        inner = node.value
        if not (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)):
            continue
        if inner.func.id != "sorted":
            continue
        if isinstance(node.slice, ast.Slice):
            advice = "`heapq.nsmallest`/`nlargest` keeps only the elements wanted"
        elif isinstance(node.slice, ast.Constant) and node.slice.value in (0, -1):
            advice = "`min()`/`max()` finds the same element in one pass"
        else:
            continue
        yield _evidence(
            unit, "sort_then_slice", node, ("C7.S4",),
            f"`{ast.unparse(node)}` sorts the whole sequence and then discards "
            f"most of it; {advice}",
            strength=Strength.LIKELY,
        )


def filter_after_transform(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A comprehension that transforms every element, then drops some.

        [f(x) for x in xs if p(f(x))]       f runs on everything, twice
        [y for y in map(f, xs) if p(y)]     f still runs on everything

    When the predicate can be expressed on `x` instead, filtering first means
    `f` runs only on the elements that survive. Reported only when the
    transform is a call, since dropping a cheap expression saves nothing.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            continue
        if not isinstance(node.elt, ast.Call):
            continue
        conditions = [c for generator in node.generators for c in generator.ifs]
        if not conditions:
            continue
        yield _evidence(
            unit, "filter_after_transform", node, ("C7.S4",),
            f"`{ast.unparse(node.elt)}` is applied to every element and the result "
            f"is then filtered; if the condition can be written on the input, "
            f"filtering first means the call runs only on what survives",
            strength=Strength.CONTEXTUAL,
        )


# -- C4.S5  expensive comparison -------------------------------------------


def expensive_comparison(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A comparison that builds a whole object to answer yes or no.

        if sorted(a) == sorted(b):      two sorts and two lists
        if str(a) == str(b):            two string conversions

    Each of these has a cheaper form -- `Counter`, a direct comparison, an
    early-exit scan -- and inside a loop the difference is paid per iteration.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Compare):
            continue
        for side in (node.left, *node.comparators):
            if (
                isinstance(side, ast.Call)
                and isinstance(side.func, ast.Name)
                and side.func.id in EXPENSIVE_COMPARISON_CALLS
                and side.args
            ):
                yield _evidence(
                    unit, "expensive_comparison", node, ("C4.S5",),
                    f"`{ast.unparse(node)}` builds a new object with "
                    f"`{side.func.id}()` only to compare it and throw it away",
                    call=side.func.id,
                    strength=Strength.LIKELY if ctx.in_loop(node) else Strength.CONTEXTUAL,
                )
                break


# -- C1.S3 / C1.S6 / C1.S7  redundant work ---------------------------------


def redundant_bool_branch(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A branch that returns the truth value it just computed.

        if x > k: return True
        else:     return False
        # -> return x > k

    Two jumps and two constant loads for something the comparison already
    produced. Tiny per execution, which is why it is advisory.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.If) or not node.orelse:
            continue
        yes, no = _single_return(node.body), _single_return(node.orelse)
        if yes is None or no is None:
            continue
        if {yes, no} == {True, False}:
            direct = ast.unparse(node.test) if yes is True else f"not ({ast.unparse(node.test)})"
            yield _evidence(
                unit, "redundant_bool_branch", node, ("C1.S3",),
                f"this branch returns True/False for a test that already produces "
                f"a boolean; `return {direct}` is the same answer without the jump",
                strength=Strength.DEFINITE,
            )


def _single_return(body: list[ast.stmt]):
    """The constant returned by a one-statement block, or None."""
    if len(body) == 1 and isinstance(body[0], ast.Return):
        value = body[0].value
        if isinstance(value, ast.Constant):
            return value.value
    return None


def dead_initialization(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A variable given a value that is overwritten before anything reads it.

        result = []           <- never read
        result = compute()

    Only reported for straight-line code at the top level of the unit, because
    an initialisation before a conditional or a loop is usually load-bearing.
    """
    body = getattr(ctx.node, "body", [])
    for index, statement in enumerate(body):
        if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1):
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name) or not ctx.is_pure(statement.value):
            continue
        for later in body[index + 1:]:
            if target.id in ctx.read_names(later):
                break
            if _rebinds(later, target.id):
                yield _evidence(
                    unit, "dead_initialization", statement, ("C1.S6",),
                    f"`{target.id}` is assigned `{ast.unparse(statement.value)}` and "
                    f"then reassigned at line {later.lineno} without being read; the "
                    f"first value is built and discarded",
                    name=target.id,
                    strength=Strength.LIKELY,
                )
                break


def _rebinds(statement: ast.stmt, name: str) -> bool:
    return (
        isinstance(statement, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == name for t in statement.targets)
    )


def single_use_temporary(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A local bound only to be returned on the next line.

        value = compute(x)
        return value

    A store and a load the interpreter cannot always elide. Advisory: the
    naming is often deliberate and worth more than the instruction.
    """
    body = getattr(ctx.node, "body", [])
    for statement, following in zip(body, body[1:]):
        if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1):
            continue
        target = statement.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if not (isinstance(following, ast.Return) and isinstance(following.value, ast.Name)):
            continue
        if following.value.id != target.id:
            continue
        uses = sum(
            1 for n in ast.walk(ctx.node)
            if isinstance(n, ast.Name) and n.id == target.id
        )
        if uses == 2:  # the store and the return
            yield _evidence(
                unit, "single_use_temporary", statement, ("C1.S7",),
                f"`{target.id}` exists only to be returned on the next line",
                name=target.id,
                strength=Strength.DEFINITE,
            )


def discarded_pure_result(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A pure call whose result is thrown away.

        sorted(rows)        computed, then dropped
        rows.sort()         mutates, so not this

    Only pure calls qualify: a call kept for its side effect is the normal case
    and is not reported.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        if not ctx.is_pure(node.value):
            continue
        yield _evidence(
            unit, "discarded_pure_result", node, ("C1.S5",),
            f"`{ast.unparse(node.value)}` has no side effects and its result is "
            f"not used, so the work it does cannot affect anything",
            strength=Strength.DEFINITE,
        )


def runtime_management_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Interpreter housekeeping called repeatedly.

        for batch in batches:
            gc.collect()        a full collection per batch

    Correct once, ruinous per iteration: a forced collection walks every live
    object, so the loop's cost grows with the heap rather than with the batch.
    """
    for node in ast.walk(ctx.node):
        if not (isinstance(node, ast.Call) and ctx.in_loop(node)):
            continue
        dotted = _dotted(node.func)
        if dotted in RUNTIME_MANAGEMENT:
            yield _evidence(
                unit, "runtime_management_in_loop", node, ("C1.S8",),
                f"`{dotted[0]}.{dotted[1]}()` manages the interpreter itself and is "
                f"called on every iteration; its cost scales with the whole process, "
                f"not with this loop's work",
                call=f"{dotted[0]}.{dotted[1]}",
                strength=Strength.DEFINITE,
            )


# -- C11.S3 / C11.S4  concurrency ------------------------------------------


def blocking_call_in_async(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A synchronous blocking call inside a coroutine.

        async def fetch_all(urls):
            for url in urls:
                r = requests.get(url)     stalls the entire event loop

    Every other coroutine waits, and the core stays awake for the duration
    while doing nothing. One of the clearest cases where energy and wall-clock
    time come apart.
    """
    if not isinstance(ctx.node, ast.AsyncFunctionDef):
        return
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Call):
            continue
        dotted = _dotted(node.func)
        if dotted in BLOCKING_IN_ASYNC:
            yield _evidence(
                unit, "blocking_call_in_async", node, ("C11.S4",),
                f"`{dotted[0]}.{dotted[1]}()` blocks, and it is inside `async def "
                f"{ctx.node.name}`; while it waits, the event loop runs nothing else "
                f"and the core stays awake for no progress",
                call=f"{dotted[0]}.{dotted[1]}",
                strength=Strength.DEFINITE,
            )


def unjoined_thread(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A thread started and never joined, in a unit that joins nothing.

        t = threading.Thread(target=work)
        t.start()                          # no t.join() anywhere

    A worker nobody waits for keeps the interpreter alive at exit and can spin
    long after its result stopped mattering.
    """
    started = [
        node for node in ast.walk(ctx.node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "start"
    ]
    if not started:
        return
    joins = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        for node in ast.walk(ctx.node)
    )
    if joins:
        return
    for node in started:
        yield _evidence(
            unit, "unjoined_thread", node, ("C11.S3",),
            f"`{ast.unparse(node)}` starts a worker that this unit never joins; "
            f"nothing here bounds how long it runs",
            strength=Strength.CONTEXTUAL,
        )


# -- C12.S1  large-stride traversal ----------------------------------------


def column_major_traversal(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Iterating a C-ordered array down its columns.

        for j in range(cols):
            total += a[:, j].sum()

    NumPy lays rows out contiguously, so a column walk touches one useful value
    per cache line. Only fires when the file imports an array library, since
    `a[:, j]` on a list of lists means something else entirely.
    """
    if not ctx.uses_arrays:
        return
    for node in ast.walk(ctx.node):
        if not (isinstance(node, ast.Subscript) and ctx.in_loop(node)):
            continue
        index = node.slice
        if not isinstance(index, ast.Tuple) or len(index.elts) < 2:
            continue
        if isinstance(index.elts[0], ast.Slice) and not isinstance(index.elts[-1], ast.Slice):
            yield _evidence(
                unit, "column_major_traversal", node, ("C12.S1",),
                f"`{ast.unparse(node)}` walks a column of a row-major array inside a "
                f"loop, so each cache line loaded yields one useful element",
                strength=Strength.CONTEXTUAL,
            )


# -- C2.S3  excessive modularization ---------------------------------------


def self_delegation_chain(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A method whose entire body is one call to another method of the same object.

        def _get_name(self):
            return self._name

        def print_name(self):
            return f"The name is {self._get_name()}"

    Every layer costs a frame push and pop. Harmless as API surface, expensive
    when the chain sits under a loop -- which is why the scan reports how deep
    the unit is reached from, and why this is `contextual` on its own.
    """
    body = getattr(ctx.node, "body", [])
    statements = [s for s in body if not isinstance(s, ast.Expr) or
                  not isinstance(s.value, ast.Constant)]  # drop the docstring
    if len(statements) != 1:
        return
    only = statements[0]
    if not isinstance(only, ast.Return) or not isinstance(only.value, ast.Call):
        return
    call = only.value
    if not (isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name)):
        return
    if call.func.value.id != "self":
        return
    yield _evidence(
        unit, "self_delegation_chain", only, ("C2.S3", "C2.S1"),
        f"`{unit.qualname}` does nothing but call `self.{call.func.attr}()`; the "
        f"extra frame is paid on every call and buys no work",
        delegate=call.func.attr,
        strength=Strength.CONTEXTUAL,
    )


RULES = [
    float_literal_on_int_data,
    constant_sequence_literal,
    global_lookup_in_loop,
    copy_in_loop,
    sort_then_slice,
    filter_after_transform,
    expensive_comparison,
    redundant_bool_branch,
    dead_initialization,
    single_use_temporary,
    discarded_pure_result,
    runtime_management_in_loop,
    blocking_call_in_async,
    unjoined_thread,
    column_major_traversal,
    self_delegation_chain,
]
