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

from ..models import Evidence, UnitRef
from ..context import (COMPREHENSION_NODES, LOOP_NODES, OPAQUE_NODES,
                       PURE_BUILTINS, PURE_METHODS, UnitContext)

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

EXPENSIVE_COMPARISON_METHODS = frozenset({"join"})
"""Method calls that build a whole object out of a sequence.

`"".join(a) == "".join(b)` concatenates both sequences in full to answer a
question `all(x == y for x, y in zip(a, b))` answers without allocating and
without reading past the first difference.  It is `str(a) == str(b)` wearing a
different spelling, and matching only bare-name calls walked past it.
"""

MIN_USES_TO_HOIST = 4
"""Reads of one global inside a loop before hoisting it is worth mentioning.

Raised from three. A module a loop reaches for three times -- `plt`, `np`, `pd`
-- is normal code, and the hoist trades one dict lookup per read against a name
the next reader has to follow. At three the rule was one of the loudest in the
suite and almost none of it was worth acting on."""

MAX_HOISTS_PER_LOOP = 2
"""How many names one loop may be reported for, worst first."""


# Operators whose result type follows their operands, so one float literal
# makes the whole expression floating point.
FLOAT_FORCING_OPS = (ast.Mult, ast.Add, ast.Sub, ast.Pow, ast.Mod)


def _evidence(unit: UnitRef, kind: str, node: ast.AST, suggests: tuple[str, ...],
              message: str, **detail) -> Evidence:
    return Evidence(
        kind=kind,
        unit=unit,
        lineno=getattr(node, "lineno", unit.lineno),
        suggests=suggests,
        message=message,
        detail=detail,
    )


def _dotted(func: ast.AST) -> tuple[str, str] | None:
    """`re.compile` -> ("re", "compile"); anything else -> None."""
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return (func.value.id, func.attr)
    return None


# -- C5.S3  over-provisioned data type -------------------------------------


def float_literal_on_int_data(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A float constant in arithmetic that would otherwise stay integer.

        [i * 3.0 for i in lst]      every product is a float
        [i * 3   for i in lst]      every product stays an int

    Small Python integers are cached and their arithmetic avoids the float
    boxing path entirely, so the `.0` costs a conversion and an allocation per
    element for a value nobody asked to be fractional.  Measured at +39.0% over
    a million integers.

    Three shapes this used to get wrong, all of them found by testing it against
    what the card claims rather than against what it did:

      * it keyed on `in_loop`, so it missed every comprehension -- including
        `[n * 3.0 for n in counts]`, which is the card's own measured example;
      * it ignored `x += 1.0`, which forces the same conversion;
      * it fired on a literal whose sibling operand is already float-valued --
        a fractional literal, a true division, or an explicit `float(...)` --
        where the result was going to be a float regardless and the `.0` costs
        nothing.
    """
    for node in ast.walk(ctx.node):
        pair = _integral_float_operand(node)
        if pair is None:
            continue
        expression, literal = pair
        if not ctx.repeats(expression):
            continue
        yield _evidence(
            unit, "float_literal_on_int_data", expression, ("C5.S3",),
            f"`{ast.unparse(expression)}` forces a float result with the literal "
            f"`{literal}`, which has no fractional part; every element pays for "
            f"a conversion and a float allocation the value does not need",
            literal=literal,
        )


def _integral_float_operand(node: ast.AST):
    """`(expression, literal)` when arithmetic is made floating by a whole-number
    constant that is not already implied by another operand."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, FLOAT_FORCING_OPS):
        operands = [node.left, node.right]
    elif isinstance(node, ast.AugAssign) and isinstance(node.op, FLOAT_FORCING_OPS):
        operands = [node.value]
    else:
        return None

    # A sibling that is already float-valued makes the result a float whatever
    # the whole-number literal does, so there is nothing to save by changing it.
    # `x / y` is true division and `float(x)` says so outright -- both were
    # being reported, and in both the `.0` forces nothing.
    if any(_is_fractional_float(operand) or _already_float(operand)
           for operand in operands):
        return None
    for operand in operands:
        if _is_integral_float(operand):
            return node, operand.value
    return None


def _already_float(node: ast.AST) -> bool:
    """Whether this operand is float-valued regardless of the literal beside it.

    `a / b` is true division and `float(x)` says so outright, so a `* 100.0`
    next to either forces nothing -- the result was going to be a float and the
    literal costs nothing to leave alone.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id == "float"
    return False


def _is_integral_float(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, float)
        and node.value.is_integer()
    )


def _is_fractional_float(node: ast.AST) -> bool:
    """A float literal with a fractional part, anywhere in this expression."""
    return any(
        isinstance(inner, ast.Constant)
        and isinstance(inner.value, float)
        and not inner.value.is_integer()
        for inner in ast.walk(node)
    )


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
    clearer name. Only a name read at least MIN_USES_TO_HOIST times per
    iteration is worth binding, and only the worst two per loop are reported.

    Each read is charged to the innermost loop that actually re-evaluates it.
    Walking every loop in turn instead used to report a name inside nested
    loops once per enclosing level, and counted the names in a `for` loop's
    iterable, which is evaluated once before the first pass.
    """
    local = ctx.assigned_names(ctx.node) | _parameter_names(ctx.node)
    counts: dict[int, dict[str, int]] = {}
    first: dict[int, dict[str, ast.AST]] = {}

    for node in ast.walk(ctx.node):
        if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)):
            continue
        if node.id in local:
            continue
        loop = _repeating_loop(ctx, node)
        if loop is None:
            continue
        seen = counts.setdefault(id(loop), {})
        seen[node.id] = seen.get(node.id, 0) + 1
        first.setdefault(id(loop), {}).setdefault(node.id, node)

    for loop in ctx.repeat_scopes:
        seen = counts.get(id(loop), {})
        worst = sorted(seen.items(), key=lambda pair: -pair[1])[:MAX_HOISTS_PER_LOOP]
        for name, uses in worst:
            if uses < MIN_USES_TO_HOIST:
                continue
            yield _evidence(
                unit, "global_lookup_in_loop", first[id(loop)][name], ("C10.S5",),
                f"`{name}` is not local to this unit and is read {uses} times inside "
                f"the loop, so each read costs a namespace dict lookup; binding it "
                f"to a local above the loop turns those into frame slot reads",
                name=name,
                uses=uses,
                loop_line=loop.lineno,
            )


def _repeating_loop(ctx: UnitContext, node: ast.AST) -> ast.AST | None:
    """The innermost repetition that re-evaluates `node` on every one of its passes.

    A `for` loop's iterable is evaluated once, before the first pass, so a name
    read there belongs to the loop *outside* it -- or to no loop at all when
    there is none.  `while` tests and loop bodies repeat as expected.

    Comprehensions count.  `[math.sqrt(x) for x in xs]` pays the same namespace
    lookup per element as the statement loop it replaces, and charging only
    statement loops meant the rule saw one and not the other.
    """
    scopes = ctx.repeats_around(node)
    while scopes:
        innermost = scopes[-1]
        if _contains(_iterable_clause(innermost), node):
            scopes = scopes[:-1]
            continue
        return innermost
    return None


def _iterable_clause(scope: ast.AST) -> ast.AST | None:
    """The part of a repetition evaluated once, before the first pass."""
    if isinstance(scope, (ast.For, ast.AsyncFor)):
        return scope.iter
    if isinstance(scope, COMPREHENSION_NODES) and scope.generators:
        return scope.generators[0].iter
    return None


def _contains(root: ast.AST | None, node: ast.AST) -> bool:
    return root is not None and any(child is node for child in ast.walk(root))


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
    """A container duplicated inside a loop by an explicit copy.

        for row in rows:
            current = defaults.copy()    a fresh copy every iteration
            current.update(row)

    Only the spellings that say `copy` and mean nothing else: `.copy()`,
    `copy.copy`, `copy.deepcopy`, and the `[:]` slice. A constructor call --
    `dict(defaults)`, `list(values)` -- is deliberately *not* one of them: it is
    the same expression a developer writes to convert a type or to build the
    result, and nothing in the syntax separates `dict(defaults)` (a copy of
    something shared) from `dict(row)` (a conversion of the element). Guessing
    between them reported correct code, so the rule no longer tries.

    Sometimes required even so -- the copy is mutated and must not be shared.
    The fact is certain; whether it is a fault is the reader's call.

    But only when the same container is copied every pass.  A name the loop
    rebinds holds a different object each iteration, so there is no shared
    container and nothing to hoist; reporting it described code it could not
    repair.
    """
    for node in ctx.own_nodes():
        if not ctx.repeats(node):
            continue
        described = None
        if isinstance(node, ast.Call):
            dotted = _dotted(node.func)
            if dotted and dotted[1] in {"copy", "deepcopy"}:
                described = f"{dotted[0]}.{dotted[1]}()"
        elif isinstance(node, ast.Subscript) and _is_full_slice(node.slice):
            described = "a `[:]` slice"

        # `row[:]` in a comprehension copies the element, and every copy is the
        # result; it does not duplicate a container the iterations share, so
        # there is nothing to hoist and nothing being copied twice.  The same
        # goes for a name the loop body rebinds each pass -- `df_sym` reassigned
        # from a lookup per iteration is a different frame every time, and the
        # copy cannot be lifted out of a loop it does not outlive.
        scopes = ctx.repeats_around(node)
        rebound = ctx.assigned_names(scopes[-1]) if scopes else set()
        if described and not (ctx.read_names(node) & (ctx.iteration_names(node) | rebound)):
            yield _evidence(
                unit, "copy_in_loop", node, ("C6.S2",),
                f"`{ast.unparse(node)}` duplicates a container on every iteration "
                f"using {described}; the copy is only needed if something mutates "
                f"it and the original must not change",
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
        elif _end_index(node.slice) is not None:
            # `[-1]` is a UnaryOp, not a negative Constant, so matching on the
            # literal value missed every "take the largest" case.
            advice = "`min()`/`max()` finds the same element in one pass"
        else:
            continue
        yield _evidence(
            unit, "sort_then_slice", node, ("C7.S4",),
            f"`{ast.unparse(node)}` sorts the whole sequence and then discards "
            f"most of it; {advice}",
        )


def _end_index(node: ast.AST) -> int | None:
    """`0` or `-1` when a subscript takes the first or last element."""
    if isinstance(node, ast.Constant) and node.value == 0:
        return 0
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and node.operand.value == 1
    ):
        return -1
    return None


def filter_after_transform(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A bulk transform whose result is filtered afterwards.

        parsed = [parse_document(p) for p in paths]      parses every path
        return [d.title for d in parsed if d.is_md]      keeps a few

    Filtering first means the transform runs on the survivors only.

    Used to fire on `[f(x) for x in xs if p(x)]`, which is the *repaired*
    order: a comprehension evaluates each generator's `if` clauses before the
    element expression, so `f` never sees a rejected element and that code is
    already optimal.  It keyed on "there is a call and there is an if" and so
    reported the fix as the fault.  Two shapes are left, both of which really
    do run the transform on every element:

    * a transform bound to a name whose single reader is a filtering
      comprehension -- if anything else reads the name, the full intermediate
      is wanted for its own sake and the filter cannot move up;
    * a comprehension that recomputes its own element expression inside its
      test, which runs the call on everything and twice on each survivor.

    Whether the reorder is *legal* still needs a human: a predicate that reads
    what the transform produced cannot move in front of it.
    """
    for node in ast.walk(ctx.node):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            if _recomputed_in_test(node):
                yield _evidence(
                    unit, "filter_after_transform", node, ("C7.S4", "C1.S4"),
                    f"`{ast.unparse(node.elt)}` is computed once for the test and "
                    f"again for the element, so it runs on every input and twice on "
                    f"each one that survives",
                )
            continue

        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        transform = _elementwise_call(node.value)
        if transform is None:
            continue

        produced = {id(n) for n in ast.walk(node.value)}
        readers = [
            n for n in ast.walk(ctx.node)
            if isinstance(n, ast.Name)
            and n.id == target.id
            and isinstance(n.ctx, ast.Load)
            and id(n) not in produced
        ]
        if len(readers) != 1:
            continue
        clause = ctx.parent_of(readers[0])
        if not isinstance(clause, ast.comprehension) or clause.iter is not readers[0]:
            continue
        if not clause.ifs:
            continue
        yield _evidence(
            unit, "filter_after_transform", node, ("C7.S4",),
            f"`{transform}` is applied to every element of `{target.id}`, and the "
            f"only thing that reads `{target.id}` filters it at line "
            f"{clause.ifs[0].lineno}; if the condition can be written on the input, "
            f"filtering first means the call runs only on what survives",
            name=target.id,
            transform=transform,
        )


def _elementwise_call(value: ast.AST) -> str | None:
    """The per-element call a bulk transform applies, or None if it is not one.

    `[f(x) for x in xs]`, `map(f, xs)` and `list(map(f, xs))` all qualify.
    `[x.field for x in xs]` does not: moving a filter in front of an attribute
    read saves nothing worth writing down.
    """
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in {"list", "tuple", "set", "sorted"}
        and len(value.args) == 1
    ):
        value = value.args[0]
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        if value.func.id == "map" and len(value.args) >= 2:
            return f"{ast.unparse(value.args[0])}()"
        return None
    if isinstance(value, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        if isinstance(value.elt, ast.Call):
            return ast.unparse(value.elt)
    return None


def _recomputed_in_test(comp: ast.AST) -> bool:
    """Whether a comprehension's element expression is also evaluated in its test."""
    if not isinstance(comp.elt, ast.Call):
        return False
    wanted = ast.dump(comp.elt)
    for generator in comp.generators:
        for test in generator.ifs:
            for sub in ast.walk(test):
                if isinstance(sub, ast.Call) and ast.dump(sub) == wanted:
                    return True
    return False


# -- C4.S5  expensive comparison -------------------------------------------


def expensive_comparison(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A comparison that builds a whole object to answer yes or no.

        if sorted(a) == sorted(b):      two sorts and two lists
        if str(a) == str(b):            two string conversions
        if "".join(a) == "".join(b):    two whole strings built to compare

    Each of these has a cheaper form -- `Counter`, a direct comparison, an
    early-exit scan -- and inside a loop the difference is paid per iteration.

    Naming the operand first changes nothing:

        left = sorted(a)
        right = sorted(b)
        return left == right

    The same two sorts are paid for the same yes or no, so a name that is bound
    once to one of these calls and read only by the comparison is followed
    through. A name read anywhere else is not: then the object has a second
    reader and was not built for the comparison alone.
    """
    aliases = _comparison_aliases(ctx)
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Compare):
            continue
        for side in (node.left, *node.comparators):
            call = None
            if isinstance(side, ast.Name):
                call = aliases.get(side.id)
            elif isinstance(side, ast.Call):
                call = side
            if not isinstance(call, ast.Call) or not call.args:
                continue
            builder = _expensive_builder(call.func)
            if builder is None:
                continue
            built = (
                f"`{ast.unparse(node)}` builds a new object with "
                f"`{builder}()` only to compare it and throw it away"
                if call is side else
                f"`{ast.unparse(node)}` compares an object built with "
                f"`{ast.unparse(call)}` and read nowhere else; naming it does "
                f"not make it cheaper than comparing directly"
            )
            yield _evidence(
                unit, "expensive_comparison", node, ("C4.S5",),
                built,
                call=builder,
            )
            break


def _expensive_builder(func: ast.AST) -> str | None:
    """The name of the object-building call at a comparison operand, if any.

    An attribute call is trusted only for the `sep.join(...)` idiom, and only
    when the separator is a literal or a plain name -- `os.path.join(...)`
    builds nothing and must not be reported.
    """
    if isinstance(func, ast.Name):
        return func.id if func.id in EXPENSIVE_COMPARISON_CALLS else None
    if (
        isinstance(func, ast.Attribute)
        and func.attr in EXPENSIVE_COMPARISON_METHODS
        and isinstance(func.value, (ast.Constant, ast.Name))
    ):
        return f"{ast.unparse(func.value)}.{func.attr}"
    return None


def _comparison_aliases(ctx: UnitContext) -> dict[str, ast.Call]:
    """Names bound once to a call and read once, so the name *is* the call.

    Both halves matter. Bound twice and the name is a slot rather than an alias;
    read twice and the object has a use beyond the comparison, which is the
    honest reason to have built it.
    """
    bindings: dict[str, int] = {name: 1 for name in _parameter_names(ctx.node)}
    reads: dict[str, int] = {}
    assigned: dict[str, ast.Call] = {}

    for node in ctx.own_nodes():
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                reads[node.id] = reads.get(node.id, 0) + 1
            else:
                bindings[node.id] = bindings.get(node.id, 0) + 1
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
        ):
            assigned[node.targets[0].id] = node.value

    return {
        name: call for name, call in assigned.items()
        if bindings.get(name) == 1 and reads.get(name) == 1
    }


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
            )


def discarded_pure_result(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A pure call whose result is thrown away.

        sorted(rows)        computed, then dropped
        rows.sort()         mutates, so not this

    Only pure calls qualify: a call kept for its side effect is the normal case
    and is not reported.

    A method call needs more than a pure-looking name.  `is_pure` matches the
    attribute alone, because it cannot know a receiver's type, and the pure
    method names collide with effectful APIs on other objects: `Thread.join`,
    `Queue.get`, `shutil.copy`.  Claiming a statement is dead is a strong claim,
    so here the receiver has to be something whose type is visible in the source
    -- a literal, or a display -- and `t.join()` is left alone.

    A discarded call guarded by `except` is not dead either.  `int(port)` alone
    in a `try` is how the stdlib asks "is this numeric", and the answer arrives
    as an exception rather than as a value; deleting it deletes the check.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        if not ctx.is_pure(node.value):
            continue
        if not _receiver_type_is_visible(node.value):
            continue
        if _guarded_by_handler(node, ctx):
            continue
        yield _evidence(
            unit, "discarded_pure_result", node, ("C1.S5",),
            f"`{ast.unparse(node.value)}` has no side effects and its result is "
            f"not used, so the work it does cannot affect anything",
        )


def _guarded_by_handler(statement: ast.Expr, ctx: UnitContext) -> bool:
    """Whether the statement sits in a `try` body that catches something.

    Only the body counts: a call in an `except` or `finally` arm is running
    normally and its result really is dropped.  A bare `try/finally` catches
    nothing, so it does not excuse the call either.
    """
    node: ast.AST | None = statement
    parent = ctx.parent_of(statement)
    while parent is not None and not isinstance(parent, OPAQUE_NODES):
        if isinstance(parent, ast.Try) and parent.handlers and node in parent.body:
            return True
        node, parent = parent, ctx.parent_of(parent)
    return False


def _receiver_type_is_visible(call: ast.Call) -> bool:
    """Whether the source shows what `call` is being made on.

    A plain function call carries its own name.  A method call only qualifies
    when the receiver is written out -- `", ".join(parts)`, `[1, 2].count(x)`
    -- because a bare `handle.get()` says nothing about what `handle` is.
    """
    if not isinstance(call.func, ast.Attribute):
        return True
    return isinstance(
        call.func.value,
        (ast.Constant, ast.JoinedStr, ast.List, ast.Tuple, ast.Set, ast.Dict),
    )


def runtime_management_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Interpreter housekeeping called repeatedly.

        for batch in batches:
            gc.collect()        a full collection per batch

    Correct once, ruinous per iteration: a forced collection walks every live
    object, so the loop's cost grows with the heap rather than with the batch.
    """
    for node in ctx.own_nodes():
        if not (isinstance(node, ast.Call) and ctx.repeats(node)):
            continue
        dotted = _dotted(node.func)
        if dotted in RUNTIME_MANAGEMENT:
            yield _evidence(
                unit, "runtime_management_in_loop", node, ("C1.S8",),
                f"`{dotted[0]}.{dotted[1]}()` manages the interpreter itself and is "
                f"called on every iteration; its cost scales with the whole process, "
                f"not with this loop's work",
                call=f"{dotted[0]}.{dotted[1]}",
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
    for node in ctx.own_nodes():
        if not (isinstance(node, ast.Subscript) and ctx.repeats(node)):
            continue
        index = node.slice
        if not isinstance(index, ast.Tuple) or len(index.elts) < 2:
            continue
        if isinstance(index.elts[0], ast.Slice) and not isinstance(index.elts[-1], ast.Slice):
            yield _evidence(
                unit, "column_major_traversal", node, ("C12.S1",),
                f"`{ast.unparse(node)}` walks a column of a row-major array inside a "
                f"loop, so each cache line loaded yields one useful element",
            )


# -- C2.S3  excessive modularization ---------------------------------------


def _forwards_own_parameters(function: ast.AST, call: ast.Call) -> bool:
    """Whether every argument is something the object or the caller already has.

    A parameter and an attribute of `self` are both forwarded: the wrapper
    contributes nothing the caller could not have supplied. A literal, a lambda
    or a computed expression is the opposite -- it is the choice the wrapper
    exists to make, and `self.load(symbol, "1m")` stops being a pass-through
    the moment `"1m"` appears.
    """
    if call.keywords:
        return False
    arguments = getattr(function, "args", None)
    parameters = set() if arguments is None else {
        a.arg for a in (
            *getattr(arguments, "posonlyargs", []),
            *arguments.args,
            *arguments.kwonlyargs,
        )
    }
    for argument in call.args:
        if isinstance(argument, ast.Name) and argument.id in parameters:
            continue
        if isinstance(argument, ast.Attribute):
            base = argument.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name) and base.id == "self":
                continue
        return False
    return True


def self_delegation_chain(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A method whose entire body is one call to another method of the same object.

        def _get_name(self):
            return self._name

        def print_name(self):
            return f"The name is {self._get_name()}"

    Every layer costs a frame push and pop. Harmless as API surface, expensive
    when the chain sits under a loop -- which is why the scan reports how deep
    the unit is reached from, and leaves the call to the reader.

    Only when the wrapper adds nothing.  These are not delegation:

        def load_m1(self, symbol):   return self.load(symbol, "1m")
        def cancel_expired(self):    return self.cancel_where(lambda o: ...)

    The extra argument is what the wrapper is *for* -- deleting it changes what
    every caller has to write, so the frame is buying something. Half of what
    this rule reported across four real repositories was that shape.
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
    if not _forwards_own_parameters(ctx.node, call):
        return
    yield _evidence(
        unit, "self_delegation_chain", only, ("C2.S3", "C2.S1"),
        f"`{unit.qualname}` does nothing but call `self.{call.func.attr}()`; the "
        f"extra frame is paid on every call and buys no work",
        delegate=call.func.attr,
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
    column_major_traversal,
    self_delegation_chain,
]
