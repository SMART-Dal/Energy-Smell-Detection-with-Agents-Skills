"""Analyzers for allocation, copying, materialisation and resource handling."""

from __future__ import annotations

import ast
from typing import Iterator

from ..models import Evidence, Strength, UnitRef
from ..context import COMPREHENSION_NODES, UnitContext

MUTABLE_DEFAULTS = (ast.List, ast.Dict, ast.Set)
MUTABLE_DEFAULT_CALLS = frozenset({"list", "dict", "set", "bytearray", "defaultdict",
                                   "Counter", "OrderedDict", "deque"})

# Functions that consume an iterable lazily, so wrapping their argument in a
# list only forces an allocation that is thrown away immediately.
LAZY_CONSUMERS = frozenset({"sum", "any", "all", "min", "max", "sorted", "set",
                            "tuple", "frozenset", "dict", "join", "enumerate", "zip"})

# The consumers above that never build a sequence of their own.  `sorted`,
# `set`, `tuple`, `frozenset` and `dict` allocate a container out of whatever
# they are handed, so replacing a list comprehension with a generator in front
# of them removes no allocation at all and adds a frame resume per element; the
# repair those shapes want is a set or dict comprehension, which is a different
# signal from this one.  Deleting a `list()` *call* in front of them is still a
# real saving, which is why only
# `eager_comprehension` narrows to this set and `redundant_materialisation`
# keeps the wider one.
STREAMING_CONSUMERS = frozenset({"sum", "any", "all", "min", "max", "join",
                                 "enumerate", "zip"})

# Consumers that stop at the first decisive element.  Building their argument
# eagerly does not only allocate: it also computes elements whose value can
# never affect the answer, which is C3.S6 on top of the materialisation.
SHORT_CIRCUIT_CONSUMERS = frozenset({"any", "all"})

RESOURCE_OPENERS = frozenset({"open", "connect", "urlopen", "Session", "socket"})

# Calls that take over the closing of a handle they are given: registration
# with an `ExitStack`, or appending to the list of handles that some caller
# walks and closes later.
OWNERSHIP_SINKS = frozenset({"append", "enter_context", "push", "callback", "register"})

# Constructors whose contents are already resident in memory, so "stream it
# instead" is not advice that applies to reading them.
MEMORY_BUFFERS = frozenset({"BytesIO", "StringIO"})


def _evidence(unit: UnitRef, kind: str, node: ast.AST, suggests: tuple[str, ...],
              message: str, strength: Strength = Strength.LIKELY, **detail) -> Evidence:
    return Evidence(
        kind=kind, unit=unit, lineno=getattr(node, "lineno", unit.lineno),
        suggests=suggests, message=message, strength=strength, detail=detail,
    )


def mutable_default_argument(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A mutable object as a parameter default, evaluated once at definition.

    Every call that mutates it leaves state behind, so the object grows for the
    lifetime of the process.  This is both a correctness bug and a slow memory
    leak, which is why it is worth reporting even outside hot paths.

    Reported whether or not this particular body mutates the default: the
    object is handed to the caller, and one caller that appends to it is enough.
    Proving that no reachable code writes to it would take whole-program
    analysis, and the repair -- default to `None`, build it in the body -- is
    cheap enough that the trade is not worth making.
    """
    if not isinstance(ctx.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return
    arguments = ctx.node.args
    for default in list(arguments.defaults) + [d for d in arguments.kw_defaults if d]:
        if not _is_mutable_default(default):
            continue
        yield _evidence(
            unit, "mutable_default_argument", default, ("C6.S7",),
            f"`{ast.unparse(default)}` is a mutable default, created once at "
            f"definition time and shared by every call",
            default=ast.unparse(default),
            strength=Strength.DEFINITE,
        )


def _is_mutable_default(node: ast.AST) -> bool:
    if isinstance(node, MUTABLE_DEFAULTS):
        return True
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in MUTABLE_DEFAULT_CALLS
    )


def unmanaged_resource(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A resource opened outside a `with`, relying on the collector to close it.

    Only reports openers whose result is bound to a plain local name and whose
    lifetime then ends inside this unit.  A bare `open(...)` in a `with` header
    is already managed, and one used inline as an argument is a different (and
    usually fine) pattern.

    The catalog's own exemptions for C6.S6 are the ones that used to be
    reported: a handle stored on `self`, returned to the caller, handed to a
    keeper such as an `ExitStack`, entered by a `with` on a later line, or
    closed in a `finally` is managed somewhere this rule cannot see.  Every one
    of those is normal code, and flagging them was most of what this rule said
    about real libraries -- numpy alone writes `ctx = open(path, "wb")`
    immediately followed by `with ctx as f:` in four separate modules.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        name = _called_name(call)
        if name not in RESOURCE_OPENERS:
            continue
        bound = {t.id for t in node.targets if isinstance(t, ast.Name)}
        if len(bound) != len(node.targets):
            # `self._handle = open(...)` or `cache[key] = open(...)`: the handle
            # is deliberately outliving the call, so its owner closes it.
            continue
        if _is_released(ctx.node, bound) or _is_handed_over(ctx.node, bound):
            continue
        yield _evidence(
            unit, "unmanaged_resource", node, ("C6.S6",),
            f"`{name}()` result is not managed by a `with` block, so the handle "
            f"is released only when the collector gets to it",
            opener=name,
            strength=Strength.LIKELY,
        )


def _called_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _is_released(scope: ast.AST, names: set[str]) -> bool:
    """Whether a handle bound to one of `names` is closed deterministically.

    Covers the explicit `handle.close()`, usually in a `finally`, and the two
    shapes where a `with` adopts a handle that was opened on an earlier line:
    `with handle:` and `with closing(handle):`.
    """
    for node in ast.walk(scope):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "close"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in names
        ):
            return True
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if names & _names_read(item.context_expr):
                    return True
    return False


def _is_handed_over(scope: ast.AST, names: set[str]) -> bool:
    """Whether the handle leaves this unit, making its lifetime someone else's.

    A returned or yielded handle belongs to the caller; one appended to a list
    of handles or entered into an `ExitStack` belongs to that keeper; one stored
    on an attribute or into a container belongs to the object holding it.
    """
    for node in ast.walk(scope):
        if isinstance(node, (ast.Return, ast.Yield)) and node.value is not None:
            if _passes_on(node.value, names):
                return True
        elif isinstance(node, ast.Call) and _called_name(node) in OWNERSHIP_SINKS:
            if any(_passes_on(argument, names) for argument in node.args):
                return True
        elif isinstance(node, ast.Assign) and _passes_on(node.value, names):
            if any(not isinstance(t, ast.Name) for t in node.targets):
                return True
    return False


def _passes_on(expression: ast.expr, names: set[str]) -> bool:
    """Whether `expression` gives a handle away rather than reading through it.

    `return handle` and `return TextIOWrapper(handle)` hand the handle to
    someone else; `return handle.read()` does not -- it takes the contents and
    leaves the handle for this unit to close.
    """
    if isinstance(expression, ast.Name):
        return expression.id in names
    if isinstance(expression, (ast.Tuple, ast.List)):
        return any(_passes_on(element, names) for element in expression.elts)
    if isinstance(expression, ast.Call):
        return any(_passes_on(argument, names) for argument in expression.args) or any(
            _passes_on(keyword.value, names) for keyword in expression.keywords
        )
    return False


def _names_read(node: ast.AST) -> set[str]:
    return {
        sub.id
        for sub in ast.walk(node)
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load)
    }


def redundant_materialisation(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """`list(...)` handed straight to something that would consume it lazily.

    Suggests C5.S4 and C6.S3, which the discriminators separate by patch shape:
    deleting a conversion call is C5.S4, changing an eager producer into a lazy
    one is C6.S3.

    Only the inline conversion counts.  Once the list is bound to a name it may
    be indexed, re-iterated or sliced, and deleting the conversion would then
    change what the code means rather than only what it allocates.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Call):
            continue
        consumer = _consumer_name(node)
        if consumer not in LAZY_CONSUMERS or not node.args:
            continue
        argument = node.args[0]
        if not (isinstance(argument, ast.Call) and _called_name(argument) == "list"):
            continue
        yield _evidence(
            unit, "redundant_materialisation", argument, _suggests_for(consumer,
                                                                      ("C5.S4", "C6.S3")),
            f"`list(...)` builds a full sequence only for `{consumer}()` to walk "
            f"it once; the conversion allocates the whole result up front",
            consumer=consumer,
            strength=Strength.LIKELY,
        )


def eager_comprehension(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A list comprehension passed directly to a consumer that streams it.

    `sum([x * 2 for x in data])` materialises the whole list; a generator
    expression does the same work without the intermediate allocation.

    Contextual rather than likely, because the saving is not reliable: measured
    on this project's own host, the list comprehension beat the generator
    expression feeding `sum()`, which pays a frame resume per element for a
    reducer written in C.  The case that holds up is a large sequence, or a
    consumer that stops early -- so the reader is being told where to look, not
    what to do.

    Restricted to consumers that never build a sequence themselves.  A
    comprehension whose result is indexed, iterated twice, measured with `len()`
    or returned is out of scope by construction: this rule only sees
    comprehensions written inline at a call site, where none of those are
    possible.
    """
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Call):
            continue
        consumer = _consumer_name(node)
        if consumer not in STREAMING_CONSUMERS or not node.args:
            continue
        argument = node.args[0]
        if not isinstance(argument, ast.ListComp):
            continue
        yield _evidence(
            unit, "eager_comprehension", argument, _suggests_for(consumer, ("C6.S3",)),
            f"a list comprehension is materialised only to be consumed once by "
            f"`{consumer}()`; a generator expression avoids the allocation",
            consumer=consumer,
            strength=Strength.CONTEXTUAL,
        )


def _consumer_name(call: ast.Call) -> str | None:
    """The lazy consumer a call site represents, or None if we cannot vouch for it.

    `_called_name` reduces `np.sum(...)` and `archive.zip(...)` to `sum` and
    `zip`, and neither of those consumes an iterable the way the builtin does --
    handing `np.sum` a generator instead of a list does not even mean the same
    thing.  So an attribute call is trusted only for the `sep.join(...)` idiom,
    and only when the separator is a literal or a plain name rather than a
    module path, which keeps `os.path.join(...)` out.
    """
    if isinstance(call.func, ast.Name):
        return call.func.id
    if (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "join"
        and isinstance(call.func.value, (ast.Name, ast.Constant))
    ):
        return "join"
    return None


def _suggests_for(consumer: str, base: tuple[str, ...]) -> tuple[str, ...]:
    """Add C3.S6 when the consumer cannot use everything its argument computed."""
    return base + ("C3.S6",) if consumer in SHORT_CIRCUIT_CONSUMERS else base


def whole_file_read(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """An unbounded `.read()` or `.readlines()` pulling a whole source into memory.

    Only the argument-less form counts.  `handle.read(65536)` is the chunked
    loop this rule would otherwise be recommending, and `parser.read(path)` is a
    configparser-style call that never touches a handle at all.  Reporting the
    bounded form was most of what this rule produced on real code: pandas' Stata
    reader walks its header with several dozen `read(n)` calls, and every one of
    them used to be reported as loading the entire file into memory.

    A read from an in-memory buffer is skipped for the same reason: the bytes
    are already resident, so there is no source left to stream from.
    """
    buffers = _memory_buffers(ctx.node)
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"read", "readlines"}:
            continue
        if node.args or node.keywords:
            continue
        if _reads_a_buffer(node.func.value, buffers):
            continue
        yield _evidence(
            unit, "whole_file_read", node, ("C6.S3", "C9.S2"),
            f"`.{node.func.attr}()` loads the entire source into memory; "
            f"streaming processes it incrementally",
            method=node.func.attr,
            strength=Strength.CONTEXTUAL,
        )


def _memory_buffers(scope: ast.AST) -> set[str]:
    """Local names bound to a buffer whose contents are already in memory."""
    names: set[str] = set()
    for node in ast.walk(scope):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if _called_name(node.value) in MEMORY_BUFFERS:
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def _reads_a_buffer(receiver: ast.expr, buffers: set[str]) -> bool:
    if isinstance(receiver, ast.Name):
        return receiver.id in buffers
    return isinstance(receiver, ast.Call) and _called_name(receiver) in MEMORY_BUFFERS


RULES = [
    mutable_default_argument,
    unmanaged_resource,
    redundant_materialisation,
    eager_comprehension,
    whole_file_read,
]
