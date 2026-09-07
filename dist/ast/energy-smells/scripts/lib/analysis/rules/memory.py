"""Analyzers for allocation, copying, materialisation and resource handling."""

from __future__ import annotations

import ast
from typing import Iterator

from ..models import Evidence, UnitRef
from ..context import COMPREHENSION_NODES, LOOP_NODES, UnitContext

MUTABLE_DEFAULTS = (ast.List, ast.Dict, ast.Set,
                    # A comprehension in a default runs once at definition time
                    # and hands every call the same object, exactly as a
                    # literal does -- and was passing through untouched.
                    ast.ListComp, ast.DictComp, ast.SetComp)
MEMORY_BUFFERS = frozenset({"BytesIO", "StringIO"})
"""Sources whose bytes are already resident, so there is nothing left to stream."""

LINE_SPLITS = frozenset({"splitlines", "split"})

MUTATING_CALLS = frozenset({"append", "remove", "insert", "pop", "extend",
                            "clear", "add", "discard", "update", "popitem"})

LINE_SEPARATORS = frozenset({"\n", "\r\n", "\r", b"\n", b"\r\n", b"\r"})
"""Exactly a line ending, and nothing that merely contains one.

`doc.read().split("\n\n")` splits into paragraphs, and a substring test for
"\n" said that was a line walk -- but iterating the handle yields single
lines, so the repair silently changes what the code produces."""

MUTABLE_DEFAULT_CALLS = frozenset({"list", "dict", "set", "bytearray", "defaultdict",
                                   "Counter", "OrderedDict", "deque"})

MUTABLE_DEFAULT_MODULES = frozenset({"collections", "typing"})
"""Receivers whose `.list()`/`.deque()` really do build a container.

`.set()` and `.list()` are builder and fluent-API methods all over Python --
`config_builder.set("initialized", True)` is not a mutable default -- so an
attribute call is trusted only where the receiver says it builds one."""

# Functions that consume an iterable lazily, so wrapping their argument in a
# list only forces an allocation that is thrown away immediately.
LAZY_CONSUMERS = frozenset({"sum", "any", "all", "min", "max", "sorted", "set",
                            "tuple", "frozenset", "dict", "enumerate", "zip"})
"""Consumers that walk their argument once, so building a list for them is waste.

`join` is not one of them, on measurement rather than on reading.  `str.join`
calls `PySequence_Fast`, which hands back a list unchanged and materialises
anything else, so `"".join(list(gen))` and `"".join(gen)` build exactly one list
either way: 0.1928 ms against 0.1927 ms over 2000 elements. There is no
allocation to remove, and the rule was claiming one."""

VARIADIC_ITERABLES = frozenset({"zip"})
"""Consumers that iterate *every* positional argument, so any of them counts."""

COMPARES_ITS_ARGUMENTS = frozenset({"min", "max"})
"""`min(a, b)` compares two values and iterates neither.

Dropping the conversion there does not save an allocation, it changes what
the call means -- `min(gen_a, gen_b)` raises `TypeError: '<' not supported
between instances of 'generator' and 'generator'`. The advice has to be
withheld, not merely re-worded."""

# The consumers above that never build a sequence of their own.  `sorted`,
# `set`, `tuple`, `frozenset`, `dict` -- and `join` -- allocate a container out
# of whatever they are handed, so replacing a list comprehension with a
# generator in front of them removes no allocation at all and adds a frame
# resume per element; the repair those shapes want is a set or dict
# comprehension, which is a different signal from this one.  Deleting a `list()`
# *call* in front of them is still a saving for the ones that copy, which is why
# `eager_comprehension` narrows to this set and `redundant_materialisation`
# keeps a wider one.
#
# `join` was in this set and measured the wrong way round: `"".join([str(x) for
# x in xs])` took 0.1695 ms against 0.1947 ms for the generator, because
# `PySequence_Fast` builds the same list internally and the generator pays a
# frame resume per element on top.  The advice was to write the slower form.
STREAMING_CONSUMERS = frozenset({"sum", "any", "all", "min", "max",
                                 "enumerate", "zip"})

# Consumers that stop at the first decisive element.  Building their argument
# eagerly does not only allocate: it also computes elements whose value can
# never affect the answer, which is C3.S6 on top of the materialisation.
SHORT_CIRCUIT_CONSUMERS = frozenset({"any", "all"})

RESOURCE_OPENERS = frozenset({"open", "connect", "urlopen", "Session", "socket",
                              "cursor"})

RESOURCE_MODULES = frozenset({
    "socket", "sqlite3", "psycopg2", "pymysql", "urllib", "request", "requests",
    "io", "os", "codecs", "gzip", "bz2", "lzma", "tarfile", "zipfile", "shelve",
    "smtplib", "ftplib", "http", "client", "db", "engine", "pool",
})
"""Receivers whose `.open()`/`.connect()` really does hand back a handle.

`Image.open(...)` shares the name and holds nothing, so the receiver decides."""

HANDLE_RECEIVERS = frozenset({
    "connection", "conn", "cnx", "session", "database", "db", "pool", "engine",
    "client", "sock", "socket", "cursor", "channel", "transport",
})
"""Receiver names that conventionally hold an open handle.

A convention, not a proof, and it is the only thing separating
`connection.cursor()` from `editor.cursor()` -- both are `<name>.cursor()` on
something this rule cannot type.  Guessing by name is what the module already
does with `RESOURCE_MODULES`; naming the guess is better than trusting every
receiver, which reported Qt signals and graph edges as leaked file handles."""

PATH_FACTORIES = frozenset({"Path", "PurePath", "PosixPath", "WindowsPath"})
"""`Path(...).open()` is how modern Python opens a file, and the receiver is a
call rather than a module name, so the module check could never see it."""

# Calls that take over the closing of a handle they are given: registration
# with an `ExitStack`, or appending to the list of handles that some caller
# walks and closes later.
OWNERSHIP_SINKS = frozenset({"append", "enter_context", "push", "callback", "register"})

# Constructors whose contents are already resident in memory, so "stream it
# instead" is not advice that applies to reading them.


def _own_nodes(scope: ast.AST) -> Iterator[ast.AST]:
    """Walk `scope` without descending into a nested definition.

    `iter_units` emits a nested function as a unit of its own, so an
    `ast.walk` from the enclosing function reported the inner function's
    statements twice: once against the unit that contains them and once
    against the unit that merely encloses it.  The second report names a line
    the reader cannot act on where they were sent, which is the worse half.
    """
    for child in ast.iter_child_nodes(scope):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield child
        yield from _own_nodes(child)


def _evidence(unit: UnitRef, kind: str, node: ast.AST, suggests: tuple[str, ...],
              message: str, **detail) -> Evidence:
    return Evidence(
        kind=kind, unit=unit, lineno=getattr(node, "lineno", unit.lineno),
        suggests=suggests, message=message, detail=detail,
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
        )


def _is_mutable_default(node: ast.AST) -> bool:
    if isinstance(node, MUTABLE_DEFAULTS):
        return True
    if not isinstance(node, ast.Call):
        return False
    if _called_name(node) not in MUTABLE_DEFAULT_CALLS:
        return False
    # Used to require a bare `Name`, so `collections.defaultdict(list)` and
    # `collections.OrderedDict()` as defaults went unreported while the
    # `from collections import ...` spelling of the same constructor was
    # caught.  But "the final attribute is enough" was wrong the other way:
    # `.set()` and `.list()` are builder-API methods everywhere in Python, and
    # `config_builder.set("initialized", True)` in a signature was read as a
    # shared mutable set.  A bare name is the constructor; an attribute has to
    # name a receiver that builds containers.
    if isinstance(node.func, ast.Name):
        return True
    return (isinstance(node.func.value, ast.Name)
            and node.func.value.id in MUTABLE_DEFAULT_MODULES)


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

    The receiver is checked, not just the method name.  `Image.open(BytesIO(...))`
    returns a PIL image and holds no operating-system handle, and matching the
    bare word `open` reported it as a leaked file -- which was every single time
    this rule fired across four real repositories.

    That check used to apply to `open` alone, and every other opener was
    trusted on its name.  `.connect()` and `.cursor()` are not rare words:

        conn = view.clicked.connect(view.refresh)   a Qt signal
        edge = graph.connect(node_a, node_b)        a graph edge
        csr = view.document.cursor()                a text cursor

    All three were reported as leaked operating-system handles.  So every
    opener now has to name a receiver that opens something: a module that does
    (`sqlite3.connect`), a `Path(...)` call, or a local already holding a
    handle -- which is what makes `conn.cursor()` still read after
    `conn = sqlite3.connect(path)`.
    """
    handles = _handle_names(ctx.node)
    for node in _own_nodes(ctx.node):
        binding = _resource_binding(node)
        if binding is None:
            continue
        targets, call = binding
        name = _called_name(call)
        if name not in RESOURCE_OPENERS or not _is_resource_opener(call, ctx, handles):
            continue
        bound = {t.id for t in targets if isinstance(t, ast.Name)}
        if len(bound) != len(targets):
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
        )


def _called_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _resource_binding(node: ast.AST):
    """`(targets, call)` for the statement forms that bind a handle to a name.

    `handle: TextIO = open(path)` and `if (stream := open(path)):` open exactly
    the same file as the plain assignment beside them; matching only
    `ast.Assign` walked past both.
    """
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
        return node.targets, node.value
    if isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and isinstance(node.value, ast.Call):
        return [node.target], node.value
    return None


def _handle_names(scope: ast.AST) -> set[str]:
    """Locals already holding an open handle, so `conn.cursor()` is trusted."""
    found: set[str] = set()
    for node in ast.walk(scope):
        binding = _resource_binding(node)
        if binding is None:
            continue
        targets, call = binding
        func = call.func
        opens = (
            (isinstance(func, ast.Name) and func.id in PATH_FACTORIES | {"open"})
            or (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                and func.value.id in RESOURCE_MODULES)
        )
        if opens:
            found.update(t.id for t in targets if isinstance(t, ast.Name))
    return found


def _is_resource_opener(call: ast.Call, ctx: UnitContext, handles: set[str]) -> bool:
    """Whether this really opens a handle, rather than sharing a method name.

    A bare `open(...)` is the builtin unless the unit rebinds the name.  An
    attribute call is trusted only for receivers that do open something --
    `socket.socket()`, `sqlite3.connect()` -- never for a class or an object of
    unknown type.
    """
    func = call.func
    if isinstance(func, ast.Name):
        if func.id in ctx.assigned_names(ctx.node):
            return False
        if func.id == "open":
            return True  # the builtin, unless the unit rebound it above
        # `Session()`, `connect()`, `socket()`, `cursor()` are ordinary words.
        # Imported from something that opens things they are the opener; bound
        # to a class of the same name from anywhere else they are not, and this
        # rule was reporting `session = Session()` as a leaked handle on the
        # strength of the word. The dotted spellings below already demand a
        # receiver that opens something; this is the same demand.
        origin = ctx.imports.get(func.id, "").split(".")[0]
        return origin in RESOURCE_MODULES
    if not isinstance(func, ast.Attribute):
        return False
    receiver = func.value
    # `Path("/var/log/audit.log").open("a")`: the receiver is a call, which is
    # the idiomatic way to open a file and the one shape a module-name check
    # can never match.
    if (isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name)
            and receiver.func.id in PATH_FACTORIES):
        return True
    # `self._conn.cursor()` is the same handle as `conn.cursor()`, so an
    # attribute receiver is judged on its last component -- which still leaves
    # `view.clicked.connect(...)` and `view.document.cursor()` out.
    if isinstance(receiver, ast.Attribute):
        return receiver.attr.lstrip("_") in HANDLE_RECEIVERS
    if not isinstance(receiver, ast.Name):
        return False
    trusted = RESOURCE_MODULES | PATH_FACTORIES | HANDLE_RECEIVERS
    return receiver.id in trusted or receiver.id in handles


def _is_released(scope: ast.AST, names: set[str]) -> bool:
    """Whether a handle bound to one of `names` is closed deterministically.

    Covers the explicit `handle.close()`, usually in a `finally`, and the two
    shapes where a `with` adopts a handle that was opened on an earlier line:
    `with handle:` and `with closing(handle):`.
    """
    for node in ast.walk(scope):
        # The bound method counts, called or not: `stack.callback(handle.close)`
        # and `atexit.register(handle.close)` schedule exactly the same close,
        # and requiring the call parentheses reported both of them.
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "close"
            and isinstance(node.value, ast.Name)
            and node.value.id in names
        ):
            return True
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                # `_passes_on`, not "mentions the name anywhere": a `with` only
                # adopts a handle it is *given*.  Reading a name off it --
                # `with file_lock(audit.name):` -- used to count as adoption
                # and silenced the leak on the line above.
                if _passes_on(item.context_expr, names):
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
        elif isinstance(node, ast.Assign) and _stores_directly(node.value, names):
            if any(not isinstance(t, ast.Name) for t in node.targets):
                return True
    return False


def _stores_directly(expression: ast.expr, names: set[str]) -> bool:
    """Whether `expression` *is* the handle rather than something read out of it.

    Storing into an attribute or a container makes its owner responsible only
    for what is stored.  `self._raw = handle` hands the handle over;
    `self.manifest = json.load(handle)` stores the parsed manifest and leaves
    the handle to this unit -- and used to be read as a hand-over, so adding
    `self.` to the target of an otherwise reported leak silenced it.
    """
    if isinstance(expression, ast.Name):
        return expression.id in names
    if isinstance(expression, (ast.Tuple, ast.List)):
        return any(_stores_directly(element, names) for element in expression.elts)
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


def redundant_materialisation(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """`list(...)` handed straight to something that would consume it lazily.

    Suggests C5.S4 and C6.S3, and the shape alone does not say which: deleting
    a conversion call is C5.S4, changing an eager producer into a lazy one is
    C6.S3.  Both are named, because the reader can tell them apart and this
    cannot.

    Only the inline conversion counts.  Once the list is bound to a name it may
    be indexed, re-iterated or sliced, and deleting the conversion would then
    change what the code means rather than only what it allocates.

    `zip(names, list(scores))` counts too, since `zip` iterates every argument
    it is given.  `min(list(a), list(b))` does not: two arguments to `min` are
    two values being compared, not one sequence being walked, and deleting the
    conversions there raises `TypeError` rather than saving anything.
    """
    for node in _own_nodes(ctx.node):
        if not isinstance(node, ast.Call):
            continue
        consumer = _consumer_name(node)
        if consumer not in LAZY_CONSUMERS:
            continue
        if consumer in COMPARES_ITS_ARGUMENTS and len(node.args) != 1:
            continue
        candidates = node.args if consumer in VARIADIC_ITERABLES else node.args[:1]
        for argument in candidates:
            if not (isinstance(argument, ast.Call) and _called_name(argument) == "list"):
                continue
            if _snapshots_a_mutated_collection(argument, ctx):
                continue
            yield _evidence(
                unit, "redundant_materialisation", argument,
                _suggests_for(consumer, ("C5.S4", "C6.S3")),
                f"`list(...)` builds a full sequence only for `{consumer}()` to "
                f"walk it once; the conversion allocates the whole result up front",
                consumer=consumer,
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

    `min([...], [...])` is excluded for the same reason as in
    `redundant_materialisation`: those are two values being compared, and
    turning the first into a generator raises `TypeError`.  A comprehension in
    a later argument of `zip` is included, having previously been missed for no
    reason but its position.

    Walks `_own_nodes` rather than `ast.walk`, so a comprehension inside a
    nested `def` is reported once -- against the function that contains it --
    instead of twice.
    """
    for node in _own_nodes(ctx.node):
        if not isinstance(node, ast.Call):
            continue
        consumer = _consumer_name(node)
        if consumer not in STREAMING_CONSUMERS or not node.args:
            continue
        if consumer in COMPARES_ITS_ARGUMENTS and len(node.args) != 1:
            continue
        candidates = node.args if consumer in VARIADIC_ITERABLES else node.args[:1]
        for argument in candidates:
            if not isinstance(argument, ast.ListComp):
                continue
            yield _evidence(
                unit, "eager_comprehension", argument,
                _suggests_for(consumer, ("C6.S3",)),
                f"a list comprehension is materialised only to be consumed "
                f"once by `{consumer}()`; a generator expression avoids the "
                f"allocation",
                consumer=consumer,
            )


def _snapshots_a_mutated_collection(conversion: ast.Call, ctx: UnitContext) -> bool:
    """Whether this `list(...)` exists to be iterated while the original changes.

        for idx, task in enumerate(list(queue)):
            if task.expired: queue.remove(task)

    The conversion is the only reason that loop is correct -- delete it and the
    iteration walks a collection that is shrinking underneath it, skipping
    elements or raising `RuntimeError`.  Not an allocation to save: a copy
    doing exactly the job a copy is for.

    The collection is matched by what the author wrote, not by a bare name.
    `list(self.queue)` guarding `self.queue.remove(task)` is the same loop as
    the one above and the commoner spelling of it, and requiring an `ast.Name`
    on both sides recognised neither -- so the rule offered to delete the one
    line keeping the iteration correct.

    The loop this asks about is the one the conversion is *written in*, which is
    not the same question `loops_around` answers.  A `for` loop's iterable runs
    once, before the loop starts, so the snapshot above is not repeated by the
    loop it protects -- and reading the repeat stack here found no loop at all
    and let the finding through.
    """
    if len(conversion.args) != 1:
        return False
    subject = conversion.args[0]
    if not isinstance(subject, (ast.Name, ast.Attribute)):
        return False
    original = ast.unparse(subject)
    for loop in _loops_written_around(conversion, ctx):
        for node in ast.walk(loop):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in MUTATING_CALLS
                    and ast.unparse(node.func.value) == original):
                return True
            if isinstance(node, ast.Delete) and any(
                isinstance(t, ast.Subscript) and ast.unparse(t.value) == original
                for t in node.targets
            ):
                return True
    return False


def _loops_written_around(node: ast.AST, ctx: UnitContext) -> list[ast.AST]:
    """Every `for`/`while` this node is lexically inside, innermost first.

    Includes the loop whose own header the node sits in, which is what separates
    it from `loops_around` -- that one counts what repeats, and a loop's iterable
    does not repeat with its body.
    """
    found: list[ast.AST] = []
    current = ctx.parent_of(node)
    while current is not None:
        if isinstance(current, LOOP_NODES):
            found.append(current)
        current = ctx.parent_of(current)
    return found


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
    """A whole source loaded, then immediately walked one line at a time.

        for line in handle.readlines():     the list exists for one pass
        lines = handle.read().splitlines()

    Both build the entire content in memory to consume it in pieces, and both
    have a form that does not -- iterating the handle yields the same lines
    without the list. Measured at 22.7% on a large file, and at 99.9% where the
    consumer stops early, since the lines after the stopping point are never
    read at all.

    One caveat travels with the repair, so the message carries it: iterating a
    handle keeps the trailing newline, and `.splitlines()` strips it. Swapping
    one for the other turns `"KEY"` into `"KEY\n"`, which a set lookup or an
    equality test will not forgive. `.readlines()` keeps it either way.

    The narrowness is the rule. An earlier version reported every argument-less
    `.read()`, which is the same shape without the precondition that makes the
    repair legal: `return response.read()` *is* the whole body, and a config or
    a JSON document has to be parsed whole. Those have no streaming form to
    recommend, and reading a file whole is the normal way to read a file. So the
    consumer has to be visible, and it has to be walking lines.
    """
    buffers = _memory_buffers(ctx.node)
    consumers = _line_consumers(ctx.node)
    for node in ast.walk(ctx.node):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"read", "readlines"} or node.args or node.keywords:
            continue
        if _reads_a_buffer(node.func.value, buffers):
            continue
        consumer = consumers.get(id(node))
        if consumer is None:
            continue
        yield _evidence(
            unit, "whole_file_read", node, ("C6.S3",),
            f"`.{node.func.attr}()` builds the whole content in memory and "
            f"{consumer} walks it a line at a time; iterating the handle "
            f"yields the same lines without the list, though it keeps the "
            f"trailing newline that `.readlines()` and `.splitlines()` differ on",
            method=node.func.attr,
        )


def _line_consumers(scope: ast.AST) -> dict[int, str]:
    """Expressions whose value is walked line by line where it is produced.

    Keyed by `id` rather than by the node, because two identical calls in one
    unit compare equal to neither each other nor themselves under `==`.
    """
    produced = _single_assignments(scope)

    def record(source: ast.AST, how: str) -> None:
        consumed.setdefault(id(source), how)
        # `lines = handle.readlines()` then `for line in lines:` is the same
        # pattern one name apart, and keying on `id()` alone could never join
        # them -- the loop iterates an `ast.Name`, the producer is an
        # `ast.Call`, and the two ids have nothing to do with each other.
        if isinstance(source, ast.Name) and source.id in produced:
            consumed.setdefault(id(produced[source.id]), how)

    consumed: dict[int, str] = {}
    for node in ast.walk(scope):
        if isinstance(node, (ast.For, ast.AsyncFor)):
            record(node.iter, "a loop")
        elif isinstance(node, ast.comprehension):
            record(node.iter, "a comprehension")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in LINE_SPLITS
            and _splits_on_lines(node)
        ):
            record(node.func.value, f"`.{node.func.attr}()`")
    return consumed


def _single_assignments(scope: ast.AST) -> dict[str, ast.AST]:
    """Names assigned exactly once in this scope, mapped to what produced them.

    Exactly once, because a name rebound later is not reliably the thing the
    loop below it walks, and this rule would rather miss than mislink.
    """
    values: dict[str, list[ast.AST]] = {}
    for node in ast.walk(scope):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name):
            values.setdefault(target.id, []).append(node.value)
    return {name: found[0] for name, found in values.items() if len(found) == 1}


def _splits_on_lines(call: ast.Call) -> bool:
    """`.splitlines()`, or a `.split()` that was given a newline to split on.

    `.split()` with no argument splits on whitespace and `.split(",")` on a
    field separator; neither is a line walk, and neither has a streaming form.
    """
    if call.func.attr == "splitlines":
        return True
    return (bool(call.args) and isinstance(call.args[0], ast.Constant)
            and call.args[0].value in LINE_SEPARATORS)


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
    whole_file_read,
    mutable_default_argument,
    unmanaged_resource,
    redundant_materialisation,
    eager_comprehension,
]
