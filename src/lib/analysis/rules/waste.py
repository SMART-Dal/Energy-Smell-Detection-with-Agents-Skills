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
import builtins
from typing import Iterator

from ..models import Evidence, UnitRef
from ..context import (COMPREHENSION_NODES, OPAQUE_NODES,
                       UnitContext)

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
FLOAT_FORCING_OPS = (ast.Mult, ast.Add, ast.Sub, ast.Pow)
"""Arithmetic where a `.0` literal makes an otherwise integer result a float.

`%` is deliberately absent. `m % 1.0` is how the fractional part of a float is
written, and the measured claim (+39% over a million integers) is about
multiplication and addition -- not about a modulo whose literal was chosen to
say "this is a float"."""


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


MUTATING_IN_PLACE = frozenset({
    "append", "extend", "insert", "remove", "pop", "clear", "sort", "reverse",
    "add", "discard", "update", "popitem", "setdefault",
})


def _mutated_in(scope: ast.AST) -> set[str]:
    """Names at the root of anything the scope changes without rebinding it.

    The *root*, so `self.path.append(n)` reports "self".  Callers compare this
    against the names an expression reads, and `self.path[:]` reads only "self";
    matching the receiver exactly would have missed it.  That is the shape this
    rule's own docstring uses as its counter-example -- a backtracking snapshot
    -- written the way it is usually written, on an attribute.

    Coarse in the safe direction: a loop that mutates any attribute of `self`
    silences a copy of any other, which loses a finding rather than proposing
    one whose repair leaves a list of aliases to a single list.
    """
    found: set[str] = set()

    def root(node: ast.AST) -> str | None:
        while isinstance(node, (ast.Attribute, ast.Subscript)):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    for node in ast.walk(scope):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATING_IN_PLACE):
            found.add(root(node.func.value))
        elif isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            found.add(root(node.value))
        elif isinstance(node, ast.Delete):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    found.add(root(target.value))
    found.discard(None)
    return found


def _escapes(scope: ast.AST, name: str) -> bool:
    """Whether the unit hands this name to anything outside itself."""
    for node in ast.walk(scope):
        if isinstance(node, (ast.Return, ast.Yield)) and isinstance(node.value, ast.Name):
            if node.value.id == name:
                return True
        elif isinstance(node, ast.Call):
            for argument in (*node.args, *(k.value for k in node.keywords)):
                inner = argument.value if isinstance(argument, ast.Starred) else argument
                if isinstance(inner, ast.Name) and inner.id == name:
                    return True
    return False


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

    An annotation counts as float-valued too.  `def compute(duration: float)`
    is the author saying what the value is, and `duration * 2.0` forces
    nothing; without reading it the rule assumed every untyped name held an
    integer, which is the assumption the whole finding rests on.
    """
    float_names = frozenset(_float_valued_names(ctx.node))
    for node in ast.walk(ctx.node):
        pair = _integral_float_operand(node, float_names)
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


def _integral_float_operand(node: ast.AST, float_names: frozenset):
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
    if any(_is_fractional_float(operand) or _already_float(operand, float_names)
           for operand in operands):
        return None
    # And a call's result is not an integer either. The finding rests entirely
    # on the claim that the other operand is integral; for a name that claim is
    # checkable -- an annotation, a binding in this unit -- and for a call it is
    # a guess with nothing behind it. It guessed wrong on
    # `returns.rolling(...).std() * np.sqrt(252.0) * 100.0`, a pandas Series of
    # floats reported as paying for a conversion and an allocation per element.
    if any(_is_opaque_operand(operand) for operand in operands):
        return None
    for operand in operands:
        if _is_integral_float(operand):
            return node, operand.value
    return None


def _is_opaque_operand(node: ast.AST) -> bool:
    """Whether this operand's type is beyond anything the rule could read.

    A call and an `await` only, not every non-name.  An attribute is a stored
    value the reader can look up in a second, and dropping those would take most
    of the rule with them; a call result is a type this rule has no route to at
    all, and it is where the one measured false positive lived.
    """
    if isinstance(node, (ast.Call, ast.Await)):
        return True
    if isinstance(node, ast.BinOp):
        return _is_opaque_operand(node.left) or _is_opaque_operand(node.right)
    return False


def _already_float(node: ast.AST, float_names: frozenset) -> bool:
    """Whether this operand is float-valued regardless of the literal beside it.

    `a / b` is true division and `float(x)` says so outright, so a `* 100.0`
    next to either forces nothing -- the result was going to be a float and the
    literal costs nothing to leave alone.
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id == "float"
    if isinstance(node, ast.Name) and node.id in float_names:
        return True
    if isinstance(node, ast.BinOp):
        return _already_float(node.left, float_names) or _already_float(node.right, float_names)
    return False


def _float_valued_names(scope: ast.AST) -> set[str]:
    """Names this unit says are floats: an annotation, or a float-valued binding.

    `def compute(duration: float)` is the author stating the type, and `* 2.0`
    on it forces nothing -- the product was always going to be a float. Without
    this the rule assumed every untyped name was an integer, which is how a
    parameter annotated `float` came to be reported.
    """
    found: set[str] = set()
    arguments = getattr(scope, "args", None)
    if arguments is not None:
        declared = [*getattr(arguments, "posonlyargs", []), *arguments.args,
                    *arguments.kwonlyargs]
        for argument in declared:
            if argument.annotation is not None and _names_a_float(argument.annotation):
                found.add(argument.arg)
    for node in ast.walk(scope):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _names_a_float(node.annotation):
                found.add(node.target.id)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and _already_float(node.value, frozenset()):
                found.add(target.id)
    return found


def _names_a_float(annotation: ast.AST) -> bool:
    root = annotation
    while isinstance(root, ast.Subscript):
        root = root.value
    if isinstance(root, ast.Attribute):
        return root.attr in {"float", "float64", "float32", "Decimal"}
    if isinstance(root, ast.Name):
        return root.id in {"float", "Decimal"}
    if isinstance(root, ast.Constant) and isinstance(root.value, str):
        return "float" in root.value.lower()
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
        # A tuple has no `append`. If the name leaves this unit -- returned,
        # yielded, or handed to something that could mutate it -- the rule
        # cannot see what happens to it next, and the repair turns a working
        # program into an `AttributeError` somewhere it never looked.
        if _escapes(ctx.node, target.id):
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
    """Whether `name` is ever appended to, assigned into, or reassigned.

    `colors += [...]` is `list.__iadd__`, an in-place extend, and read as never
    mutated. As a tuple it stops being in-place, and `tuple += list` raises
    outright -- so an augmented assignment disqualifies the rewrite, and a
    `for` target rebinding the name does too.

    Rebinding by plain assignment does not. `modes = ["r", "w"]` replaced by
    `modes = ["rb", "wb"]` in a branch mutates no list; both literals convert
    independently, which is why the count of bindings is deliberately not
    consulted here.
    """
    for node in ast.walk(scope):
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return True
        if isinstance(node, (ast.For, ast.AsyncFor)):
            for inner in ast.walk(node.target):
                if isinstance(inner, ast.Name) and inner.id == name:
                    return True
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

    And only names a person would actually bind.  Two kinds are excluded
    because the repair is not something anyone writes:

        _float = float          rebinding a builtin
        _np = np                rebinding an imported module

    Both are real dict lookups and both are technically hoistable, and neither
    is advice: `float` read thirteen times in a loop is what arithmetic on
    mixed types looks like, and aliasing `np` makes the next reader work out
    what `_np` is. What is left is the case the card is about -- a module-level
    table or helper the loop reaches for, where `labels = FIELD_LABELS` above
    the loop reads as well as it runs.

    The threshold below matters more than the rule. Reporting every non-local
    name read in a loop produced 45 hits across `requests` -- more than every
    other analyzer combined, and mostly imported helpers read once per
    iteration, where a hoist saves one dict lookup against the cost of a
    clearer name. Only a name read at least MIN_USES_TO_HOIST times per
    iteration is worth binding, and only the worst two per loop are reported.

    Each read is charged to the innermost loop that actually re-evaluates it.
    Walking every loop in turn instead used to report a name inside nested
    loops once per enclosing level, and counted the names in a `for` loop's
    iterable, which is evaluated once before the first pass.  Annotations are
    skipped for the same reason as the iterable: `batch: List[Order] = []` in a
    loop reads `List` and `Order`, and a function-local annotation is never
    evaluated, so neither read happens.
    """
    local = ctx.assigned_names(ctx.node) | _parameter_names(ctx.node)
    unbindable = _NOT_WORTH_BINDING | set(ctx.module_aliases) | _imported_modules(ctx.node)
    counts: dict[int, dict[str, int]] = {}
    first: dict[int, dict[str, ast.AST]] = {}

    for node in ast.walk(ctx.node):
        if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)):
            continue
        if node.id in local or node.id in unbindable:
            continue
        if id(node) in ctx.annotation_nodes:
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


_NOT_WORTH_BINDING = frozenset(dir(builtins))
"""Builtins. Real lookups, but `_len = len` above a loop is not advice."""


def _imported_modules(scope: ast.AST) -> set[str]:
    """Names bound to a *module* by an import, which nobody rebinds.

    `import numpy as np` makes `np` a global read on every use, and aliasing it
    to a local is a lookup saved against a name the next reader has to chase.
    `from numpy import array` is different -- `array` is a function, and binding
    a function above a loop is ordinary code -- so only plain `import` counts.
    """
    found: set[str] = set()
    for node in ast.walk(scope):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.asname or alias.name.split(".")[0])
    return found


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
    repair.  A name the loop *mutates* is the same case and was not covered:

        for n in nums:
            path.append(n)
            results.append(path[:])
            recurse(); path.pop()

    `path` is never rebound, so it looked invariant, and the copy looked like a
    duplicate of one unchanging container.  It is a snapshot of a value that is
    different on every pass, and deleting it leaves a list of empty lists.
    """
    for node in ctx.own_nodes():
        if not ctx.repeats(node):
            continue
        described = None
        if isinstance(node, ast.Call):
            func = node.func
            # `manager.default_config.copy()` and `self.config.copy()` are the
            # same copy as `defaults.copy()`, and a receiver test that demanded
            # a bare name missed every one of them.
            # A second argument means it is not a container copy at all:
            # `shutil.copy(src, dst)` copies a *file*, and the only thing it has
            # in common with `defaults.copy()` is the word. Every real spelling
            # here takes at most the object being copied.
            if (isinstance(func, ast.Attribute) and func.attr in {"copy", "deepcopy"}
                    and len(node.args) <= 1 and not node.keywords):
                described = f"{ast.unparse(func.value)}.{func.attr}()"
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
        rebound |= _mutated_in(scopes[-1]) if scopes else set()
        if described and _copy_is_consumed(node, ctx, scopes):
            continue
        if described and not (ctx.read_names(node) & (ctx.iteration_names(node) | rebound)):
            yield _evidence(
                unit, "copy_in_loop", node, ("C6.S2",),
                f"`{ast.unparse(node)}` duplicates a container on every iteration "
                f"using {described}; the copy is only needed if something mutates "
                f"it and the original must not change",
            )


def _copy_is_consumed(node: ast.AST, ctx: UnitContext, scopes) -> bool:
    """Whether the copy's result is changed or kept, so each pass needs its own.

    The guard above asks whether the thing being *copied* changes. This asks
    what happens to the *copy*, which is the half that decides whether hoisting
    is even legal:

        for row in rows:
            current = defaults.copy()
            current.update(row)          # changed
            out.append(current)          # and kept

    Hoisting that leaves every row sharing one dict. The rule used to report it
    while staying silent on the character-for-character identical version
    written `dict(defaults)` -- silent because a constructor is not a copy
    spelling -- so the same code got two different answers depending on
    punctuation. The answer that matches the repair is to report neither.
    """
    if not scopes:
        return False
    parent = ctx.parent_of(node)
    while parent is not None and not isinstance(parent, (ast.Assign, ast.AnnAssign)):
        if isinstance(parent, (ast.stmt,)):
            break
        parent = ctx.parent_of(parent)
    if not isinstance(parent, (ast.Assign, ast.AnnAssign)):
        return False
    targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
    names = {t.id for t in targets if isinstance(t, ast.Name)}
    if not names:
        return False
    loop = scopes[-1]
    return bool(names & (_mutated_in(loop) | {n for n in names if _escapes(loop, n)}))


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
            if not _keeps_a_prefix_or_suffix(node.slice):
                continue
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


def _keeps_a_prefix_or_suffix(node: ast.Slice) -> bool:
    """Whether a slice takes the k smallest or the k largest, and nothing else.

    The rule is that most of the sort is thrown away, so the slice has to be
    the throwing-away. `[::2]` keeps half of it in order, `[::-1]` keeps all of
    it reversed, and `[3:]` keeps everything but the smallest three -- for none
    of those is `heapq.nsmallest` the same answer, and the message claiming
    they "discard most of it" was simply false.
    """
    if node.step is not None:
        return False
    if node.lower is None:
        # `[:k]` only when k is a positive literal. `[:-1]` reads as a prefix
        # and keeps all but one element, so the sort is not thrown away and
        # `nsmallest` is not the same answer -- the opposite of this rule.
        if isinstance(node.upper, ast.UnaryOp) and isinstance(node.upper.op, ast.USub):
            return False
        return node.upper is not None            # [:k]
    if node.upper is None:                       # [-k:]
        return (isinstance(node.lower, ast.UnaryOp)
                and isinstance(node.lower.op, ast.USub))
    return False


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

    C6.S1, "objects created and thrown away that never needed to exist", which
    is what the sorted lists and the built strings above are.  It used to name
    C4.S5, whose card is about a *type or identity check* asked once per element
    -- `isinstance`, `type(x) ==`, `hasattr` -- and no comparison this rule
    reports is one of those.  Nothing detects C4.S5 now, which is the honest
    state of it and how fifteen other root causes already stand.

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
    # `own_nodes`, not `ast.walk`: a comparison inside a nested `def` belongs to
    # that def, which `iter_units` emits as a unit of its own, and walking into
    # it reported the same line against both.
    for node in ctx.own_nodes():
        if not isinstance(node, ast.Compare):
            continue
        sides = [(side, _built_by(side, aliases)) for side in (node.left, *node.comparators)]
        for side, call in sides:
            if call is None:
                continue
            # `str(user_id) == "1001"` is a type conversion against a literal --
            # the ordinary way to compare an int to text -- and it was reported
            # as an object built and thrown away. There is nothing to take
            # away: the conversion *is* the comparison. A non-literal on the
            # other side is a different matter, since both sides are then work.
            if all(_is_literal(other) for other, _ in sides if other is not side):
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
                unit, "expensive_comparison", node, ("C6.S1",),
                built,
                call=builder,
            )
            break


def _is_literal(node: ast.AST) -> bool:
    """A constant or a display of constants, i.e. nothing that costs anything."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(_is_literal(e) for e in [*node.keys, *node.values] if e is not None)
    return False


def _built_by(side: ast.AST, aliases: dict) -> ast.Call | None:
    """The object-building call at one operand, directly or through a name."""
    call = aliases.get(side.id) if isinstance(side, ast.Name) else side
    if not isinstance(call, ast.Call) or not call.args:
        return None
    return call if _expensive_builder(call.func) else None


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
    produced. Tiny per execution; the measurement says whether it matters.

    The message names the `return` that goes with the branch, because the
    early-return spelling reads as though only the `if` were being replaced:

        if a(x): return True
        if b(x): return True      <- reported here
        return False

    The repair is to replace *this* `if` and the `return` under it, which leaves
    the guard above untouched.  Read as a whole-body rewrite it looks like it
    drops that guard, and a careful reader read it that way.
    """
    for node in ctx.own_nodes():
        pair = _bool_ternary_or_assign(node)
        if pair is None:
            continue
        test, kind = pair
        yield _evidence(
            unit, "redundant_bool_branch", node, ("C1.S3",),
            f"{kind} hands back True/False for `{test}`, which already produces "
            f"a boolean; `bool({test})` is the same answer without the branch",
        )

    for node, yes, no in _bool_branches(ctx.node):
        if {yes, no} != {True, False}:
            continue
        test = ast.unparse(node.test)
        if yes is not True and isinstance(node.test, ast.UnaryOp) and isinstance(
                node.test.op, ast.Not):
            # `if not token: return False` / `return True` answers `bool(token)`.
            # Negating the negation reads as `not (not token)`, which is correct
            # and is not advice anyone would take.
            inner = node.test.operand
            direct = (ast.unparse(inner) if _yields_a_bool(inner)
                      else f"bool({ast.unparse(inner)})")
        elif yes is not True:
            direct = f"not ({test})"
        elif _yields_a_bool(node.test):
            direct = test
        else:
            # `if settings.get("api_key"): return True` is a *truthiness* test,
            # and `return settings.get("api_key")` hands back the key. That
            # breaks `-> bool`, breaks `is True`, and was what this rule
            # advised for every test that is not itself a comparison.
            direct = f"bool({test})"
        yield _evidence(
            unit, "redundant_bool_branch", node, ("C1.S3",),
            f"this branch and the `return` that follows it hand back True/False "
            f"for a test that already produces a boolean; replacing both with "
            f"`return {direct}` is the same answer without the jump"
            if not node.orelse else
            f"this branch returns True/False for a test that already produces "
            f"a boolean; `return {direct}` is the same answer without the jump",
        )


def _bool_branches(scope: ast.AST):
    """Yield `(if_node, true_branch_value, false_branch_value)`.

    Two spellings, because they compile to the same thing and the second is the
    commoner one by far -- an early-return guard has no `else`, so requiring
    `node.orelse` skipped every `if not token: return False` / `return True`.
    """
    for node in ast.walk(scope):
        if isinstance(node, ast.If) and node.orelse:
            yes, no = _single_return(node.body), _single_return(node.orelse)
            if yes is not None and no is not None:
                yield node, yes, no
            continue
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for first, second in zip(body, body[1:]):
            if not isinstance(first, ast.If) or first.orelse:
                continue
            yes, no = _single_return(first.body), _single_return([second])
            if yes is not None and no is not None:
                yield first, yes, no


def _bool_ternary_or_assign(node: ast.AST):
    """`(test, description)` for the two spellings `_bool_branches` cannot see.

        return True if x else False        an IfExp, not an If
        if c: flag = True
        else: flag = False                 assignment, not return

    Both are the same two constant loads around a test that already produced a
    boolean, and both are common enough that leaving them out made the rule
    look like it was about `return` rather than about the branch.
    """
    if isinstance(node, ast.IfExp):
        if _constant_bool(node.body) is True and _constant_bool(node.orelse) is False:
            return ast.unparse(node.test), "a conditional expression"
        return None
    if not (isinstance(node, ast.If) and node.orelse):
        return None
    yes, no = _sole_bool_assignment(node.body), _sole_bool_assignment(node.orelse)
    if yes is None or no is None:
        return None
    (yes_name, yes_val), (no_name, no_val) = yes, no
    if yes_name != no_name or (yes_val, no_val) != (True, False):
        return None
    return ast.unparse(node.test), f"assigning `{yes_name}` in both arms"


def _constant_bool(node: ast.AST):
    """`True`/`False` for a literal boolean, else None."""
    return node.value if isinstance(node, ast.Constant) and isinstance(
        node.value, bool) else None


def _sole_bool_assignment(body: list):
    """`(name, value)` when a block is exactly one `name = True/False`."""
    if len(body) != 1 or not isinstance(body[0], ast.Assign):
        return None
    stmt = body[0]
    if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
        return None
    value = _constant_bool(stmt.value)
    return None if value is None else (stmt.targets[0].id, value)


def _yields_a_bool(node: ast.AST) -> bool:
    """Whether an expression is already a `bool`, not merely truthy."""
    if isinstance(node, ast.Compare):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, ast.BoolOp):
        return all(_yields_a_bool(v) for v in node.values)
    if isinstance(node, ast.Constant):
        return isinstance(node.value, bool)
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in {"bool", "isinstance", "issubclass", "callable",
                                 "hasattr", "any", "all"})


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
    for node in ctx.own_nodes():
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

    Both spellings, like `blocking_call_in_async` beside it: `from gc import
    collect` binds the function itself, so the call is an `ast.Name` and reading
    only `module.attr` saw half of them.
    """
    for node in ctx.own_nodes():
        if not (isinstance(node, ast.Call) and ctx.repeats(node)):
            continue
        managed = _runtime_management_name(node.func, ctx)
        if managed:
            yield _evidence(
                unit, "runtime_management_in_loop", node, ("C1.S8",),
                f"`{managed}()` manages the interpreter itself and is "
                f"called on every iteration; its cost scales with the whole process, "
                f"not with this loop's work",
                call=managed,
            )


def _runtime_management_name(func: ast.AST, ctx: UnitContext) -> str | None:
    """The housekeeping call this is, reached through its module or imported."""
    dotted = _dotted(func)
    if dotted in RUNTIME_MANAGEMENT:
        return f"{dotted[0]}.{dotted[1]}"
    if not isinstance(func, ast.Name):
        return None
    origin = (ctx.imports.get(func.id) or "").split(".")[0]
    if (origin, func.id) in RUNTIME_MANAGEMENT:
        return f"{origin}.{func.id}"
    return None


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
    # `own_nodes` rather than `ast.walk`: a nested `def` is a unit of its own,
    # and a blocking call inside one runs wherever that function is called --
    # `threading.Thread(target=worker).start()` puts it on another thread
    # entirely, which is the repair rather than the fault.
    for node in ctx.own_nodes():
        if not isinstance(node, ast.Call):
            continue
        named = _blocking_name(node.func, ctx)
        if named is None:
            continue
        yield _evidence(
            unit, "blocking_call_in_async", node, ("C11.S4",),
            f"`{named}()` blocks, and it is inside `async def "
            f"{ctx.node.name}`; while it waits, the event loop runs nothing else "
            f"and the core stays awake for no progress",
            call=named,
        )


def _blocking_name(func: ast.AST, ctx: UnitContext) -> str | None:
    """The blocking call this is, whether reached through its module or not.

    `from time import sleep` binds the function directly, so the call is an
    `ast.Name` and a rule reading only `module.attr` never saw it -- which is
    the spelling anyone writes who calls it more than twice.
    """
    dotted = _dotted(func)
    if dotted in BLOCKING_IN_ASYNC:
        return f"{dotted[0]}.{dotted[1]}"
    if not isinstance(func, ast.Name):
        return None
    origin = ctx.imports.get(func.id)
    if origin and (origin.split(".")[0], func.id) in BLOCKING_IN_ASYNC:
        return f"{origin.split('.')[0]}.{func.id}"
    return None


# -- C12.S1  large-stride traversal ----------------------------------------


PANDAS_ACCESSORS = frozenset({"iloc", "loc", "iat", "at"})
"""Label-and-position accessors whose overhead hides any memory-layout effect."""


def column_major_traversal(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Iterating a C-ordered array down its columns.

        for j in range(cols):
            total += a[:, j].sum()

    NumPy lays rows out contiguously, so a column walk touches one useful value
    per cache line. Only fires when the file imports an array library, since
    `a[:, j]` on a list of lists means something else entirely.

    A pandas accessor is not an array subscript and is skipped.  The shape is
    identical -- `df.iloc[:, j]` matches `[slice, non-slice]` exactly -- but the
    reasoning does not survive it: the accessor's own overhead dwarfs anything
    the memory layout contributes.  Over a 400x400 frame, column-wise measured
    21.61 ms against 21.19 ms row-wise, a 2% spread that is noise, while the
    same traversal on the underlying ndarray ran 0.81 ms and 0.68 ms.  The
    finding promised a saving that is not there in either direction.

    `.values` and `.to_numpy()` are deliberately not in the skip list: those
    hand back a real ndarray, and the cache argument applies again.
    """
    if not ctx.uses_arrays:
        return
    for node in ctx.own_nodes():
        if not (isinstance(node, ast.Subscript) and ctx.repeats(node)):
            continue
        if (isinstance(node.value, ast.Attribute)
                and node.value.attr in PANDAS_ACCESSORS):
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

    Nor is a decorated method, or one whose delegate a subclass overrides.
    """
    # A decorator changes what the method *is*: `@property` makes it an
    # attribute read, `@cached_property` a memoised one, a hook registration
    # makes it something the framework calls. None of them is a frame the
    # caller chose to pay, and `method_ignores_self` and `trivial_delegation`
    # both check this while this rule did not.
    if getattr(ctx.node, "decorator_list", []):
        return
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
    # `def process(self, data): return self._do_process(data)` with a subclass
    # supplying `_do_process` is the template-method pattern: the frame is the
    # extension point. Shallow, like `method_ignores_self`'s use of it -- only
    # overrides visible in this module are known.
    if call.func.attr in ctx.overridden_methods:
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
