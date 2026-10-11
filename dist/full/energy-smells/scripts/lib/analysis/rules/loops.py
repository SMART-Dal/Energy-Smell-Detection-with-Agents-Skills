"""Analyzers for work done inside loops.

Loops are where energy smells concentrate, because anything wasteful in a loop
body is paid once per iteration.  These rules find *facts* ("this expression
does not change across iterations"), not verdicts -- deciding whether a fact is
actually a smell needs context that only the reader has.
"""

from __future__ import annotations

import ast
from typing import Iterator

from ..models import Evidence, UnitRef
from ..context import (
    COMPREHENSION_NODES, LOOP_NODES, OPAQUE_NODES, PURE_BUILTINS, PURE_METHODS,
    UnitContext, is_cheap_expression,
)
from .waste import _copy_is_consumed

# C5.S1 puts the break-even for a set at "roughly a dozen elements"; below it,
# scanning a sequence costs less than hashing the thing you are looking for.
SMALL_SEQUENCE = 12

# Module-level `re` functions that compile or parse something reusable.
RE_FUNCTIONS = frozenset({
    "compile", "search", "match", "findall", "sub", "subn",
    "fullmatch", "split", "finditer",
})


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


REPORTABLE_INVARIANTS = (
    ast.Call, ast.Subscript,
    ast.ListComp, ast.SetComp, ast.DictComp, 
)
"""What is worth naming as loop-invariant.

Hoisting a bare name or a literal buys nothing. A comprehension is here
because rebuilding a collection per iteration is the expensive case, and it is
the comprehension -- not the `range()` inside it -- that gets hoisted."""


def loop_invariant_expression(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Non-trivial pure expressions whose value cannot change across iterations.

    The highest-value analyzer in the suite.
    Only reports calls and subscripts -- hoisting a bare name or a literal buys
    nothing, and reporting those would bury the real findings in noise.

    A whole comprehension is reportable too, not only calls and subscripts.
    `{i for i in range(1, k, 2)}` inside a loop rebuilds the same set on every
    iteration, and the thing to hoist is the comprehension -- charging its
    `range(...)` to the comprehension instead lands on the one clause a
    comprehension evaluates once, so the finding disappeared entirely.

    Comprehensions count as scopes, not just `for` and `while`.
    `[[0] * len(SMELLS) for _ in range(n)]` recomputes `len(SMELLS)` once per
    element exactly as the statement loop would, and the repair is the same --
    bind it to a name on the line above.  Keying on statement loops alone made
    the rule blind to the commonest way a loop is written in Python.
    """
    for scope in ctx.repeat_scopes:
        rewritten = ctx.assigned_names(scope)
        mutated = _mutated_paths(scope)
        reported: list[ast.AST] = []
        for node in ctx.per_iteration_nodes(scope):
            if not isinstance(node, REPORTABLE_INVARIANTS):
                continue
            if ctx.repeats_around(node)[-1:] != (scope,):
                continue  # belongs to a nested scope; that scope will report it
            if isinstance(node, ast.Call) and _is_trivial_call(node):
                continue
            if is_cheap_expression(node) and not _reads_by_key(node):
                # Hoisting a builtin call on scalars -- `len(x)`, `float("nan")`,
                # `range(len(b))` -- saves a call; see `is_cheap_expression`.
                # A lookup by key is kept: `C3S4_genuinely_quadratic` hoists
                # `points[i]` and `matrix[i]` out of an inner loop and measured
                # +16.4% and +19.4%. The two C3.S2 samples that hoist a `len()`
                # measured 25-42% on loops doing nothing else; leaving `len` out
                # is a decision about what real loops look like, not a reading.
                continue
            if not ctx.is_pure(node):
                continue
            if _builds_fresh_container(node) and _is_kept(node, ctx, scope):
                continue
            if _is_view_call(node) and not _tested_for_membership(node, ctx):
                # `for k, v in patch.items():` in an outer loop builds a view,
                # which costs a call. `key in mapping.keys()` is the C4.S8
                # shape, measured at 35-55%, and stays.
                continue
            if _leaves_the_loop(ctx, node, scope):
                continue
            # Only the names the expression reads from *outside* itself matter.
            # A comprehension binds its own targets, and counting those made
            # `{i for i in range(1, k, 2)}` look like it varied with the loop
            # because `i` is assigned somewhere inside it.
            free = ctx.read_names(node) - ctx.assigned_names(node)
            if free & rewritten:
                continue
            if _reads_mutated_path(ctx, node, mutated):
                continue
            if any(_contains(outer, node) for outer in reported):
                continue  # already covered by a larger invariant expression
            reported.append(node)
            yield _evidence(
                unit, "loop_invariant_expression", node, ("C3.S2",),
                f"`{ast.unparse(node)}` does not change across loop iterations "
                f"but is re-evaluated every time",
                expression=ast.unparse(node),
                loop_line=scope.lineno,
                depth=ctx.repeat_depth(node),
            )


def _reads_by_key(node: ast.AST) -> bool:
    """Whether the expression indexes something: `d[k]`, `rows[i]`, `d.get(k)`."""
    return any(
        (isinstance(sub, ast.Subscript) and not isinstance(sub.slice, ast.Slice))
        or (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
            and sub.func.attr == "get")
        for sub in ast.walk(node)
    )


FRESH_CONTAINER_CALLS = frozenset({
    "list", "dict", "set", "bytearray", "deque", "defaultdict", "OrderedDict", "Counter",
})


def _builds_fresh_container(node: ast.AST) -> bool:
    """A new mutable container: a constructor, a `.copy()`, or a comprehension.

    Each pass getting its own is often the point. `changed = dict(kwargs)`
    followed by `changed[key] = value` reads as invariant -- nothing it reads
    changes -- but hoisting it hands every pass the same dict.
    """
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
        return True
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in FRESH_CONTAINER_CALLS
    return isinstance(func, ast.Attribute) and func.attr in {"copy", "deepcopy"}


def _is_kept(node: ast.AST, ctx: UnitContext, scope: ast.AST) -> bool:
    """Whether each pass's fresh container outlives the pass, so it must be its own.

    Three ways it is kept, each of which hoisting would turn into one object
    shared by every pass:

        changed = dict(kwargs); changed[k] = v      bound, then changed or kept
        update_stats(dict(TRACKED), live)           handed to a call
        {arm: {s: 0 for s in S} for arm in arms}    part of what the loop builds

    Literal displays are see-through: a list inside a dict that is appended is
    appended too.
    """
    if isinstance(scope, COMPREHENSION_NODES) and _within_element(node, scope, ctx):
        return True
    top = node
    parent = ctx.parent_of(top)
    while isinstance(parent, (ast.Dict, ast.List, ast.Tuple, ast.Set, ast.keyword)):
        top, parent = parent, ctx.parent_of(parent)
    if isinstance(parent, ast.Call) and top is not parent.func and not ctx.is_pure(parent):
        return True
    if isinstance(parent, (ast.Return, ast.Yield)):
        return True
    return _copy_is_consumed(top, ctx, (scope,))


def _within_element(node: ast.AST, comprehension: ast.AST, ctx: UnitContext) -> bool:
    """Whether `node` is part of the element a comprehension produces."""
    produced = ([comprehension.key, comprehension.value]
                if isinstance(comprehension, ast.DictComp) else [comprehension.elt])
    current = node
    while current is not None and current is not comprehension:
        if any(current is part for part in produced):
            return True
        current = ctx.parent_of(current)
    return False


def _is_view_call(node: ast.AST) -> bool:
    """`d.keys()`, `d.values()`, `d.items()` on a plain name or attribute."""
    return (isinstance(node, ast.Call) and not node.args and not node.keywords
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"keys", "values", "items"}
            and is_cheap_expression(node.func.value))


def _tested_for_membership(node: ast.AST, ctx: UnitContext) -> bool:
    parent = ctx.parent_of(node)
    return isinstance(parent, ast.Compare) and any(
        isinstance(op, (ast.In, ast.NotIn)) and right is node
        for op, right in zip(parent.ops, parent.comparators))


def _leaves_the_loop(ctx: UnitContext, node: ast.AST, scope: ast.AST) -> bool:
    """Whether the expression sits in a `return` or `raise` inside the loop.

    That statement ends the loop, so what it evaluates runs once per entry to
    the loop, not once per pass: `return {"reason": raw[:200]}` written inside
    a retry loop is not recomputed by the loop.
    """
    current = ctx.parent_of(node)
    while current is not None and current is not scope:
        if isinstance(current, (ast.Return, ast.Raise)):
            return True
        current = ctx.parent_of(current)
    return False


def _is_trivial_call(call: ast.Call) -> bool:
    """`len(x)` on a rewritten name is the point; `int()` on a literal is not.

    A method call is never trivial, even with no arguments.  Counting arguments
    alone treated `region.strip().lower()` as having nothing to be invariant in
    and dropped the whole family of zero-argument method calls on an invariant
    receiver -- which are the expensive ones, since the receiver is an operand
    in everything but name.
    """
    if isinstance(call.func, ast.Attribute):
        return False
    return not call.args and not call.keywords


def _mutated_paths(scope: ast.AST) -> set[str]:
    """Receiver paths whose *contents* change inside `scope`, as written.

    `assigned_names` only sees rebinding, so a work-list traversal
    (`queue.extend(...)` under `while position < len(queue)`) and an in-place
    compaction (`del values[i]` under `while i < len(values)`) both left the
    length looking invariant.  Both are C3.S2 counter-examples where hoisting
    the call is a behaviour change, not an optimisation.

    Paths, not root names.  This used to walk every receiver down to its root
    `Name`, so `self.log.debug(row)` recorded `self` and suppressed every other
    `self.*` expression in the loop -- `len(self.limits)`, `self.cfg.mode`, all
    of it.  One logging call is enough to trigger that, and in method-heavy
    code most loops contain one, so the rule was quietly declining to look at
    the receiver it sees most often.

    Recording `self.log` instead lets the caller ask whether the expression it
    is about to report actually overlaps what changed.  A bare receiver still
    records the bare name: `self.reset()` can touch anything under `self`, and
    `queue.extend(...)` rebinds nothing but changes `queue` itself, so both
    keep their whole subtree suppressed.  `repeated_lookup_in_loop` already
    reasons about chains this way; this brings the two into line.
    """
    paths: set[str] = set()

    def path_of(node: ast.AST) -> str | None:
        while isinstance(node, ast.Subscript):
            node = node.value          # `self.cache[k] = v` changes `self.cache`
        if isinstance(node, (ast.Name, ast.Attribute)):
            try:
                return ast.unparse(node)
            except Exception:          # pragma: no cover - unparse is total here
                return None
        return None

    for node in ast.walk(scope):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr not in PURE_METHODS:
                paths.add(path_of(node.func.value))
        elif isinstance(node, ast.Delete):
            paths.update(path_of(target) for target in node.targets)
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            paths.update(path_of(t) for t in targets
                         if isinstance(t, (ast.Subscript, ast.Attribute)))
    paths.discard(None)
    return paths


def _overlaps(read: str, mutated: str) -> bool:
    """Whether reading `read` can observe a change made through `mutated`.

    True when they are the same path, when the read reaches inside what
    changed (`self.log.level` against `self.log`), and when the read is a
    prefix of it (`self` against `self.log`) -- the last because handing the
    whole object to something else exposes the part that moved.
    """
    return (read == mutated
            or read.startswith(mutated + ".")
            or mutated.startswith(read + "."))


def _reads_mutated_path(ctx: UnitContext, node: ast.AST, mutated: set[str]) -> bool:
    """Whether any receiver path `node` reads overlaps something `scope` changes.

    Each `Name` load is grown outward into the longest attribute chain that is
    still inside `node`, so `len(self.limits)` is tested as `self.limits`
    rather than as `self`.
    """
    if not mutated:
        return False
    for sub in ast.walk(node):
        if not (isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load)):
            continue
        top = sub
        while top is not node:
            parent = ctx.parent_of(top)
            if isinstance(parent, ast.Attribute) and parent.value is top:
                top = parent
            else:
                break
        read = ast.unparse(top)
        if any(_overlaps(read, path) for path in mutated):
            return True
    return False


def _contains(outer: ast.AST, inner: ast.AST) -> bool:
    """Whether `inner` is a sub-expression of `outer`."""
    return any(node is inner for node in ast.walk(outer))


def string_concat_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Text accumulated inside a loop -- but only quadratic for some accumulators.

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

    What makes an accumulator textual is decided from *where it starts*, not
    from the right-hand side.  Keying on the value was the original mistake and
    it made the rule nearly useless: `self.buf += render_row(row)` -- the card's
    own example -- has an unrecognisable call on the right and never fired, and
    neither did `out += chunk`, which is the commonest form there is.  An
    accumulator initialised to `""` or `b""` is text whatever gets added to it.

    Both spellings count: `s += x` and `s = s + x` allocate identically.
    Numeric accumulators are excluded throughout: `n += 1` is fine.
    """
    accumulators = _text_accumulators(ctx.node)

    for node, enclosing in ctx.inside_loops():
        pair = _concatenation(node)
        if pair is None:
            continue
        target, value = pair
        name = _target_name(target)
        # Adding a number to text raises, so `+= 1` is a counter whatever else
        # the container holds: one `snapshot["message"] = "..."` used to make
        # every `snapshot[...] += 1` in the unit look like string growth.
        if isinstance(value, ast.Constant) and type(value.value) in (int, float, complex):
            continue
        if name not in accumulators and not _looks_stringy(value):
            continue
        if _looks_numeric(value) and name not in accumulators:
            continue

        loop = enclosing[-1]
        if isinstance(value, ast.JoinedStr):
            # No in-place path exists for an f-string, so the accumulator's
            # reference count is irrelevant and every spelling is quadratic.
            yield _evidence(
                unit, "string_concat_in_loop", node, ("C10.S4",),
                f"`{name}` is rebuilt by an f-string that interpolates itself "
                f"inside a loop; f-strings always allocate a new object, so "
                f"this copies the whole value every iteration even when the "
                f"accumulator is a plain local",
                accumulator=name, accumulator_kind="fstring",
                loop_line=loop.lineno,
            )
            continue
        if isinstance(target, (ast.Attribute, ast.Subscript)):
            through = "an attribute" if isinstance(target, ast.Attribute) else "a subscript"
            yield _evidence(
                unit, "string_concat_in_loop", node, ("C10.S4",),
                f"`{name}` is grown by concatenation inside a loop; because it "
                f"is stored through {through}, CPython cannot resize it in "
                f"place and copies the whole value every iteration",
                accumulator=name, accumulator_kind="aliased",
                loop_line=loop.lineno,
            )
        elif isinstance(target, ast.Name):
            if _name_is_retained_in(loop, target.id, skip=node):
                yield _evidence(
                    unit, "string_concat_in_loop", node, ("C10.S4",),
                    f"`{target.id}` is grown by concatenation inside a loop and "
                    f"a reference to it is kept there, so it survives to the next "
                    f"pass and each iteration copies the whole value",
                    accumulator=target.id, accumulator_kind="escaping",
                    loop_line=loop.lineno,
                )
            else:
                yield _evidence(
                    unit, "string_concat_in_loop", node, ("C10.S4",),
                    f"`{target.id}` is grown by concatenation inside a loop, but "
                    f"it is a plain local with no other reference, so CPython "
                    f"resizes it in place and the loop is already linear -- "
                    f"reject unless this runs on another runtime",
                    accumulator=target.id, accumulator_kind="local",
                    loop_line=loop.lineno,
                )


def _concatenation(node: ast.AST):
    """`(target, value)` if this statement appends to its own target.

    Covers three spellings:

        s += x                  AugAssign
        s = s + x               Assign whose value re-reads the target
        s = f"{s}{x}"           Assign whose f-string interpolates the target

    The first two allocate identically.  The third does not, and is worse --
    see `_is_fstring_accumulation`.
    """
    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
        return node.target, node.value
    if (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.value, ast.JoinedStr)
            and _is_fstring_accumulation(node.targets[0], node.value)):
        return node.targets[0], node.value
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.value, ast.BinOp)
        and isinstance(node.value.op, ast.Add)
    ):
        target = node.targets[0]
        rendered = _target_name(target)
        # `res = res + "[" + r + "]"` parses left-associatively, so the
        # accumulator is at the bottom of the left spine, not at `value.left`.
        # Comparing only the immediate operand meant every concatenation of
        # more than two parts -- the commonest way anyone builds a line --
        # silently failed to match its own target.
        if _target_name(_leftmost_operand(node.value)) == rendered:
            return target, node.value.right
        if _target_name(node.value.right) == rendered:
            return target, node.value.left
    return None


def _is_fstring_accumulation(target: ast.AST, value: ast.JoinedStr) -> bool:
    """Whether an f-string rebuilds its own target: `s = f"{s}{x}"`.

    This is the same quadratic growth as `s = s + x` to a reader, and a worse
    one to the interpreter.  `+=` and `+` both reach CPython's
    `unicode_concatenate`, which resizes the string in place when its refcount
    is 1, so a plain local accumulator stays linear.  An f-string is compiled
    to `FORMAT_VALUE`/`BUILD_STRING`, which always builds a new object, so
    there is no in-place path to hit and no refcount that would help.

    Measured on CPython 3.10, 20k against 40k iterations:

        out += p             1.15 ->   2.10 ms   linear
        out = out + p        1.01 ->   2.08 ms   linear
        out = f"{out}{p}"   41.16 -> 260.18 ms   QUADRATIC

    That is why the caller does not run the local/escaping distinction over
    this shape: unlike `+=`, it is quadratic for every accumulator, including
    the plain local the other two spellings are safe with.
    """
    rendered = _target_name(target)
    if rendered is None:
        return False
    return any(
        isinstance(part, ast.FormattedValue)
        and _target_name(part.value) == rendered
        for part in value.values
    )


def _leftmost_operand(node: ast.AST) -> ast.AST:
    """The bottom of a chain of `+`: `((a + b) + c)` -> `a`."""
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        node = node.left
    return node


def _text_accumulators(scope: ast.AST) -> set[str]:
    """Targets this unit assigns a string or bytes value to, by rendered name.

    Two shapes seed one: a direct assignment of a str/bytes constant, and
    `container.setdefault(key, "")`, which is how a subscript accumulator is
    usually started.
    """
    found: set[str] = set()
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, (str, bytes)):
                found.update(_target_name(t) for t in node.targets)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.annotation, ast.Name):
            if node.annotation.id in {"str", "bytes"}:
                found.add(_target_name(node.target))
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setdefault"
            and len(node.args) == 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, (str, bytes))
        ):
            found.add(f"{_target_name(node.func.value)}[...]")
    return found



def _target_name(node: ast.AST) -> str:
    """Readable name for an assignment target, for the evidence message."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_target_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return f"{_target_name(node.value)}[...]"
    return "the accumulator"


RETAINING_METHODS = frozenset({"append", "appendleft", "add", "insert",
                               "extend", "push", "put"})
"""Methods that keep the object they are handed after they return."""


def _name_is_retained_in(loop: ast.AST, name: str, skip: ast.AST | None = None) -> bool:
    """Whether the loop keeps a reference to `name` that outlives the iteration.

    This used to ask the much weaker question "is `name` read anywhere in the
    loop", on the reasoning that any load takes a second reference and defeats
    CPython's in-place resize.  Half of that is true: the resize happens only
    when the string's refcount is 1 at the moment of the `+=`.  But a load on
    another line holds its reference only while that expression is being
    evaluated, and has dropped it again long before the next `+=`.

    Measured on CPython 3.10, 20k against 40k iterations, wall clock:

        out += p                                1.12 ->    2.09 ms   linear
        out += p; if len(out) > N: ...          2.22 ->    4.48 ms   linear
        out += p; noop(out)                     2.10 ->    4.11 ms   linear
        out += p; other = out                  41.03 ->  266.77 ms   QUADRATIC
        out += p; kept.append(out)            569.92 -> 2204.44 ms   QUADRATIC

    So a bare read and an ordinary call argument stay linear, and the rule was
    reporting both as "a second reference exists and each iteration copies the
    whole value" -- a claim the machine disagrees with by a factor of 500.
    What actually costs is a reference that is still alive on the next pass:
    bound to another name, stored in a container, or yielded.

    `noop(out)` and `kept.append(out)` are the same shape to a parser, so the
    call case is split by method name rather than by what the callee does.  A
    plain call is read as transient, which is right for `flush(out)` and wrong
    for a callee that stores its argument.  That direction is the safe one to
    be wrong in: it downgrades a finding to the branch that says the loop is
    already linear, rather than asserting a copy that is not happening.

    `skip` excludes the accumulating statement itself, because `s = s + x`
    reads `s` as part of the accumulation.  Counting that as a retained
    reference would grade every long-form concatenation as aliased.
    """
    skipped = {id(node) for node in ast.walk(skip)} if skip is not None else set()

    def reads_it(tree: ast.AST) -> bool:
        return any(isinstance(n, ast.Name) and n.id == name
                   and isinstance(n.ctx, ast.Load) and id(n) not in skipped
                   for n in ast.walk(tree))

    for node in ast.walk(loop):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            # `other = out` -- the new binding outlives this pass.  A store back
            # into the accumulator itself is the accumulation, not a reference.
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if reads_it(node.value) and not all(
                    isinstance(tgt, ast.Name) and tgt.id == name for tgt in targets):
                return True
        elif isinstance(node, (ast.Yield, ast.YieldFrom)):
            if node.value is not None and reads_it(node.value):
                return True
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in RETAINING_METHODS and any(
                    reads_it(arg) for arg in node.args):
                return True
    return False


def _looks_stringy(node: ast.AST) -> bool:
    """Best-effort check that an expression produces text.

    A secondary signal only.  What an accumulator *is* comes from where it was
    initialised (`_text_accumulators`); this catches the cases where the
    accumulator was not initialised in this unit but the value is unmistakable.
    """
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, bytes))
    if isinstance(node, ast.JoinedStr):  # f-string
        return True
    if isinstance(node, ast.BinOp):
        return _looks_stringy(node.left) or _looks_stringy(node.right)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in {
            "str", "repr", "format", "chr", "bytes", "hex", "oct",
        }:
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr in {
            "join", "format", "strip", "lstrip", "rstrip", "lower", "upper",
            "decode", "encode", "replace",
        }:
            return True
    return False


def _looks_numeric(node: ast.AST) -> bool:
    """Best-effort check that an expression produces a number.

    Used only to keep a counter out of the report when nothing else identifies
    the accumulator, so `counts[key] += 1` stays quiet.
    """
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float, complex)) and not isinstance(
            node.value, bool
        )
    if isinstance(node, ast.UnaryOp):
        return _looks_numeric(node.operand)
    if isinstance(node, ast.BinOp):
        return _looks_numeric(node.left) and _looks_numeric(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in {"len", "int", "float", "sum", "abs", "round", "ord"}
    return False


MIN_DOTS_TO_CACHE = 2
"""How deep a chain must be before binding it to a local is worth saying.

One dot -- `parts.append`, `stats.get`, `self.count` -- is how every Python
programmer reaches an attribute, and caching it saves one lookup per access.
Measured, that is `C8S3_bound_method_alias`: 10.6% in a loop doing nothing but
the call, inside the 15% this scan treats as no effect. Two dots and more --
`config.limits.maximum` -- saves a lookup per link, and measured 38-73%.
Where the loop also does real work both shrink (`C8S3_body_dominates`, 5-14%),
which no rule can see, so the depth is the line that can be drawn."""

MIN_RESOLUTIONS_TO_CACHE = 3
"""Times one attribute chain is walked in a loop before caching it is worth saying.

Raised from two. Resolving `labels.iloc` twice costs two dict lookups against a
local binding the next reader has to carry, which is not a finding -- it is the
shape of ordinary code, and reporting it buried the chains that really are
walked five or six times."""


def repeated_lookup_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Attribute chains or globals resolved repeatedly inside a loop body.

    Each `a.b.c` costs a dict lookup per level, and each global costs a scope
    chain walk.  Only chains of two dots or more (`MIN_DOTS_TO_CACHE`) that
    are resolved at least `MIN_RESOLUTIONS_TO_CACHE` times and never rewritten
    in the loop are reported.

    Chains rooted at an imported module -- `np.searchsorted`, `pd.isna`,
    `math.sqrt` -- are left alone.  Nothing here asks anyone to bind `np`
    itself to a local, and it would be incoherent to ask for
    `searchsorted = np.searchsorted` one dot later.
    They are also where the advice pays least: a module attribute is reached
    through a plain dict, with no instance `__dict__`, no MRO walk and no
    descriptor, and the calls behind those names are the ones doing real work.
    `C8S3_body_dominates` measured 10% for a body that only formats a string;
    a body calling into pandas leaves the saving far below any noise floor.

    That exclusion is also why C10.S5 is no longer suggested here.  It reads
    "a global or builtin re-resolved through the module namespace", and nothing
    this rule reports now touches the module namespace -- what is left is an
    instance `__dict__`, a type, its bases, and possibly a descriptor.  The tag
    was holding the finding down to C10.S5's 19.8%, because an ambiguous fact
    is worth its cheapest reading; unambiguous, it is worth C8.S3's 46.2%.

    One chain is one finding.  Three things used to multiply that:
    `self.limits.window.low` read twice was reported three times, once per
    prefix; a chain inside a loop nest was reported once per enclosing loop; and
    a chain the loop itself assigns to was reported even though the card's whole
    point is that a local binding has to stay valid.

    The nest is walked innermost first, so a chain read only inside an inner
    loop is reported against *that* loop.  Outermost first put the finding on
    the outer loop and then said "resolved N times inside the loop" with the
    inner loop's count, which understates it by however many times the inner
    loop runs -- a true number attached to the wrong loop.  The repair is
    unchanged either way, because a binding made above the inner loop is
    re-made each outer pass and stays valid.

    Reads inside a `def` or `lambda` written in the loop are not counted.  The
    closure is built per pass but the chain is resolved whenever it is finally
    called, which may be once, later, or never, so binding above the loop saves
    nothing there.  `ctx.owns` covers the `def` half; `lambda` is not one of
    `context.OPAQUE_NODES`, so its body is walked with the unit and has to be
    excluded here.
    """
    reported_at: dict[int, set[str]] = {}
    inner_first = sorted(ctx.loops, key=lambda l: -len(ctx.loops_around(l)))
    for loop in inner_first:
        rewritten = ctx.assigned_names(loop)
        rebound = _rebound_chains(loop)
        covered = set().union(
            *(reported_at.get(id(inner), set())
              for inner in ctx.loops if loop in ctx.loops_around(inner)),
            set(),
        )
        deferred = {id(inner) for lam in ast.walk(loop)
                    if isinstance(lam, ast.Lambda) for inner in ast.walk(lam)}
        seen: dict[str, list[ast.AST]] = {}
        for node in ast.walk(loop):
            if not isinstance(node, ast.Attribute) or not isinstance(node.ctx, ast.Load):
                continue
            if not ctx.owns(node) or id(node) in deferred:
                continue
            chain = _attribute_chain(node)
            if chain is None or chain.count(".") < 1:
                continue
            if chain.split(".")[0] in rewritten:
                continue
            if chain.split(".")[0] in ctx.module_aliases:
                continue
            if id(node) in ctx.annotation_nodes:
                continue
            if any(prefix in rebound for prefix in _prefixes(chain)):
                continue
            seen.setdefault(chain, []).append(node)

        mine: set[str] = set()
        for chain, nodes in seen.items():
            if len(nodes) < MIN_RESOLUTIONS_TO_CACHE or chain in covered:
                continue
            if chain.count(".") < MIN_DOTS_TO_CACHE:
                continue
            # Every use is a method call: binding `append = self.items.append`
            # is the bound-method alias `C8S3_bound_method_alias` measured at
            # 10.6%, however many dots lead to it.
            if all(isinstance(ctx.parent_of(n), ast.Call) and ctx.parent_of(n).func is n
                   for n in nodes):
                continue
            # A prefix is only its own finding when it is resolved more often
            # than any chain built on it -- otherwise it is the same lookup.
            longer = max((len(rest) for other, rest in seen.items()
                          if other.startswith(chain + ".")), default=0)
            if len(nodes) <= longer:
                continue
            mine.add(chain)
            yield _evidence(
                unit, "repeated_lookup_in_loop", nodes[0], ("C8.S3",),
                f"`{chain}` is resolved {len(nodes)} times inside the loop; each "
                f"access walks the attribute chain again",
                chain=chain,
                occurrences=len(nodes),
                loop_line=loop.lineno,
            )
        reported_at[id(loop)] = covered | mine


def _prefixes(chain: str) -> Iterator[str]:
    """`a.b.c` -> `a.b.c`, `a.b`, `a`: every binding a local alias would depend on."""
    parts = chain.split(".")
    for stop in range(len(parts), 0, -1):
        yield ".".join(parts[:stop])


def _rebound_chains(loop: ast.AST) -> set[str]:
    """Attribute chains the loop stores to or deletes.

    `self.total = self.total + x` reads the chain twice, and binding it to a
    local before the loop would read a value the loop then replaces.
    """
    found: set[str] = set()
    for node in ast.walk(loop):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)):
            chain = _attribute_chain(node)
            if chain is not None:
                found.add(chain)
    return found


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
    """`x in some_list` inside a loop: linear scan where a set would be O(1).

    A sequence short enough to count in the source is left alone.  C5.S1 puts
    the break-even at roughly a dozen elements and gives
    `request.method in ("GET", "HEAD", "OPTIONS")` as correct code; reporting
    every tuple literal made the rule fire on that, which is the fastest way to
    teach a reader to skip it.

    The haystack may be a name the module binds rather than the unit, since a
    table of allowed values is usually a module constant.  It may also be a
    parameter the author annotated `list` -- an annotation is a statement about
    what the value is, and ignoring it lost every `def f(pool: list)` case.
    """
    for node in ctx.own_nodes():
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], (ast.In, ast.NotIn)):
            continue
        if not ctx.runs_repeatedly(node):
            continue
        haystack = node.comparators[0]
        if not _is_sequence_valued(haystack, ctx):
            continue
        if _is_small_sequence(haystack, ctx):
            continue
        enclosing = ctx.repeats_around(node)
        if enclosing:
            where = "on every iteration"
        else:
            # No loop here: the repeats belong to a caller, so saying "every
            # iteration" would send the reader looking for a loop this file
            # does not contain.
            where = (f"on every call, and this unit is called from "
                     f"{ctx.entry_depth} level(s) of loop elsewhere")
        yield _evidence(
            unit, "membership_test_on_sequence", node, ("C5.S1", "C5.S2", "C3.S4"),
            f"membership test `{ast.unparse(node)}` scans a sequence linearly "
            f"{where}; a set or dict index would be constant-time",
            haystack=ast.unparse(haystack),
            loop_line=getattr(enclosing[-1], "lineno", unit.lineno) if enclosing else unit.lineno,
        )


def _is_sequence_valued(node: ast.AST, ctx: UnitContext) -> bool:
    """Whether an expression plausibly holds a list/tuple rather than a set/dict."""
    if isinstance(node, ast.Name):
        return _binds_sequence(node.id, ctx) or _annotated_sequence(node.id, ctx)
    return _is_literal_sequence(node)


SEQUENCE_ANNOTATIONS = frozenset({"list", "tuple", "List", "Tuple", "Sequence"})


def _annotated_sequence(name: str, ctx: UnitContext) -> bool:
    """Whether a parameter of this unit is annotated as a list or tuple."""
    arguments = getattr(ctx.node, "args", None)
    if arguments is None:
        return False
    declared = [
        *getattr(arguments, "posonlyargs", []),
        *arguments.args,
        *arguments.kwonlyargs,
    ]
    for argument in declared:
        if argument.arg != name or argument.annotation is None:
            continue
        return _annotation_root(argument.annotation) in SEQUENCE_ANNOTATIONS
    return False


NULLABLE_WRAPPERS = frozenset({"Optional", "Union"})


def _annotation_root(node: ast.AST) -> str | None:
    """`list[int]` -> "list", `typing.List[str]` -> "List".

    `Optional[list[str]]` and `list[str] | None` both mean a list that may be
    absent, and both used to answer "Optional" or nothing at all -- so the one
    habit of admitting a value can be missing hid the sequence underneath it.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        if _annotation_root(node.value) in NULLABLE_WRAPPERS:
            return _first_sequence_arg(node.slice)
        return _annotation_root(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _first_sequence_arg(node)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _annotation_root(_parse_annotation(node.value))
    return None


def _parse_annotation(text: str) -> ast.AST | None:
    """A quoted annotation as a tree, so `"Optional[list[str]]"` reads like the
    unquoted form.

    Forward references and `if TYPE_CHECKING` imports make quoted annotations
    ordinary in typed code, and splitting the string on "[" only ever saw the
    outermost name -- which for a nullable list is the wrapper, never the list.
    """
    try:
        parsed = ast.parse(text.strip(), mode="eval").body
    except (SyntaxError, ValueError):
        return None
    return None if isinstance(parsed, ast.Constant) else parsed


def _first_sequence_arg(node: ast.AST) -> str | None:
    """The first branch of a union or `Optional[...]` that names a sequence."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        branches = [node.left, node.right]
    elif isinstance(node, ast.Tuple):
        branches = list(node.elts)
    else:
        branches = [node]
    for branch in branches:
        root = _annotation_root(branch)
        if root in SEQUENCE_ANNOTATIONS:
            return root
    return None


def _binds_sequence(name: str, ctx: UnitContext) -> bool:
    """Look for an assignment in the unit that gives `name` a list/tuple value."""
    return any(_is_literal_sequence(value) for value in _bindings_of(name, ctx))


def _bindings_of(name: str, ctx: UnitContext) -> list[ast.AST]:
    """Every value assigned to `name`, from the unit or failing that the module.

    The module is only consulted when the unit never assigns the name, so a
    local of the same name always wins.
    """
    local = [
        node.value
        for node in ast.walk(ctx.node)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    ]
    # `roles: list[str] = [...]` is an `ast.AnnAssign`, and looking only for
    # `ast.Assign` meant annotating the very thing this rule reasons about was
    # enough to hide it.
    local += [
        node.value
        for node in ast.walk(ctx.node)
        if isinstance(node, ast.AnnAssign) and node.value is not None
        and isinstance(node.target, ast.Name) and node.target.id == name
    ]
    if local:
        return local
    module_value = ctx.module_bindings.get(name)
    return [module_value] if module_value is not None else []


def _is_literal_sequence(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Tuple, ast.ListComp)):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        # `["read", "write", "admin"] + load_extra_scopes()` is the C5.S1 repair
        # site itself, and matching only bare literals walked straight past it.
        return _is_literal_sequence(node.left) or _is_literal_sequence(node.right)
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "tuple", "sorted"}
    )


def _is_small_sequence(node: ast.AST, ctx: UnitContext) -> bool:
    """Whether the haystack is a literal short enough to scan faster than hash.

    Only a literal we can count answers this; anything assembled at run time is
    of unknown size and stays reportable.  That includes the accumulator:

        unique = []              # a literal, and it counts zero elements
        for item in lst:
            if item not in unique:
                unique.append(item)

    `unique` is empty *at the binding* and holds one entry per distinct item by
    the end, so counting the literal answered a question nobody asked and
    silenced the commonest quadratic loop there is.  A name that is appended to
    is of unknown size however it was seeded.
    """
    if isinstance(node, ast.Name):
        if _is_grown(node.id, ctx):
            return False
        bindings = _bindings_of(node.id, ctx)
        if len(bindings) != 1:
            return False  # rebound elsewhere, so its size is not settled here
        node = bindings[0]
    return isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) <= SMALL_SEQUENCE


GROWING_METHODS = frozenset({"append", "extend", "insert", "add", "update"})


def _is_grown(name: str, ctx: UnitContext) -> bool:
    """Whether the unit ever adds to this name after binding it."""
    for node in ast.walk(ctx.node):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in GROWING_METHODS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == name
        ):
            return True
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            return True
    return False


def index_based_iteration(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """`for i in range(len(xs))` where the index is only used to read `xs[i]`.

    "Only" is the whole rule, and it was not being checked.  Any subscript
    anywhere in the loop whose slice happened to be the index counted, without
    asking what was being done with it, so all of these were reported and the
    repair does not reach any of them:

        for i in range(len(items)):  items[i] = items[i].strip()
        for i in range(len(items)):
            if items[i] == target: return i
        for i in range(len(points)): d = points[i] - points[i - 1]

    A write-back cannot become `for item in items` -- rebinding the loop
    variable does not touch the list.  A neighbour lookup needs the offset.
    Those two still disqualify: a Store subscript, or the index inside any
    arithmetic, and the rule declines.

    An index that escapes needs `enumerate`, and that case is now reported
    rather than dropped.  `for i in range(len(xs)): print(i, xs[i])` is the
    textbook `enumerate` shape and C3.S1's own territory, but every use of the
    index that was not a Load subscript used to abandon the whole loop, so the
    commonest repair the card names was the one shape the rule stayed silent
    on.  A use that merely passes the index along as a value -- to a call, a
    return, a tuple, a comparison -- keeps the finding and changes the repair.

    Indexing a second sequence is not disqualifying, only differently
    repairable: `total += abs(first[i] - second[i])` is `zip(first, second)`,
    and the message says so rather than claiming direct iteration would do.

    Comprehension generators count as well as `for` statements: the index-driven
    form is just as common written as `[grid[i][i] for i in range(len(grid))]`.
    """
    for scope, target, iterable in _iteration_clauses(ctx):
        if not isinstance(target, ast.Name):
            continue
        driven = _range_len_argument(iterable)
        if driven is None:
            continue
        sequence, slice_form = driven
        index = target.id

        indexed: set[str] = set()
        spent_elsewhere = False
        carried = False
        wrote_back = False
        for node in ast.walk(scope):
            if not (isinstance(node, ast.Name) and node.id == index
                    and isinstance(node.ctx, ast.Load)):
                continue
            parent = ctx.parent_of(node)
            if (isinstance(parent, ast.Subscript)
                    and parent.slice is node
                    and isinstance(parent.ctx, ast.Load)):
                indexed.add(ast.unparse(parent.value))
                continue
            if isinstance(parent, (ast.BinOp, ast.UnaryOp)):
                # A neighbour offset: `xs[i - 1]` needs the arithmetic, which
                # neither direct iteration nor `enumerate` can express.
                spent_elsewhere = True
                break
            if isinstance(parent, ast.Subscript) and parent.slice is node:
                # A write-back: `items[i] = items[i].strip()`. Direct iteration
                # cannot express it -- rebinding the loop variable leaves the
                # list untouched -- but `enumerate` can, and it still removes
                # the read half. Only when the same sequence is also *read* at
                # the index, since that read is what there is to remove.
                if ast.unparse(parent.value) == sequence:
                    wrote_back = True
                    continue
                spent_elsewhere = True
                break
            # The index is handed on as a plain value: `enumerate` supplies it.
            carried = True
        if spent_elsewhere or not indexed:
            continue

        others = sorted(indexed - {sequence})
        if wrote_back:
            repair = (f"`enumerate({sequence})` gives the element without a "
                      f"second lookup, and keeps the index the write-back needs")
        elif slice_form:
            repair = f"`{slice_form}` walks those elements without an index"
        elif carried and others:
            repair = (f"`enumerate(zip({sequence}, {', '.join(others)}))` walks "
                      f"them together and still hands back the index")
        elif carried:
            repair = (f"`enumerate({sequence})` hands back the index and the "
                      f"item together, so the index costs no lookup")
        elif others:
            repair = (f"`zip({sequence}, {', '.join(others)})` walks them "
                      f"together without an index")
        else:
            repair = "iterating the sequence directly avoids an index lookup per item"
        yield _evidence(
            unit, "index_based_iteration", scope, ("C3.S1",),
            f"iterating `{ast.unparse(iterable)}` and indexing back into it; {repair}",
            sequence=sequence,
            index=index,
            also_indexed=others,
        )


def _iteration_clauses(ctx: UnitContext):
    """Yield `(scope, target, iterable)` for every `for` and every comprehension
    generator in the unit, so a rule can treat both spellings alike."""
    for node in ctx.own_nodes():
        if isinstance(node, (ast.For, ast.AsyncFor)):
            yield node, node.target, node.iter
        elif isinstance(node, COMPREHENSION_NODES):
            for generator in node.generators:
                yield node, generator.target, generator.iter


def _len_call(node: ast.AST) -> str | None:
    """Return `xs` for `len(xs)`."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        return None
    if node.func.id != "len" or len(node.args) != 1:
        return None
    return ast.unparse(node.args[0])


def _int(node: ast.AST):
    """The value of an integer literal, or None.

    `-1` is a `UnaryOp` around `Constant(1)` in the tree, not `Constant(-1)`:
    the folding happens at compile time, long after this sees it. Reading only
    `Constant` made every reverse walk invisible, since `range(len(xs) - 1, -1,
    -1)` is negative literals in two of its three arguments.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _int(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    return None


def _range_len_argument(node: ast.AST):
    """`(xs, slice_form)` for a `range(...)` driven by `len(xs)`.

    `slice_form` is the spelling that walks the same elements directly, and is
    empty for the plain case where the sequence itself does:

        range(len(xs))                  ->  ("xs", "")
        range(0, len(xs), 2)            ->  ("xs", "xs[::2]")
        range(len(xs) - 1, -1, -1)      ->  ("xs", "reversed(xs)")

    A stride and a reverse walk were declined outright before, on the grounds
    that they are not `range(len(xs))`. They are not, but the index is doing
    the same job in all three and Python spells all three without one; what
    changes is the repair, which is the thing worth saying rather than a reason
    to stay quiet.
    """
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        return None
    if node.func.id != "range" or not 1 <= len(node.args) <= 3:
        return None
    args = node.args

    if len(args) == 1:
        seq = _len_call(args[0])
        return (seq, "") if seq else None

    step = _int(args[2]) if len(args) == 3 else 1
    if step is None or step == 0:
        return None

    if step > 0:
        # `range(0, len(xs))` and `range(0, len(xs), k)`.
        if _int(args[0]) != 0:
            return None
        seq = _len_call(args[1])
        if seq is None:
            return None
        return (seq, "") if step == 1 else (seq, f"{seq}[::{step}]")

    # A reverse walk: `range(len(xs) - 1, -1, -1)`.
    if step != -1 or _int(args[1]) != -1:
        return None
    start = args[0]
    if not (isinstance(start, ast.BinOp) and isinstance(start.op, ast.Sub)
            and _int(start.right) == 1):
        return None
    seq = _len_call(start.left)
    return (seq, f"reversed({seq})") if seq else None


def append_only_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A loop whose whole body is one `.append()`: a comprehension in disguise.

    Only when the list being appended to is the *same* list every time.  These
    are not comprehensions in disguise:

        for threshold in thresholds:
            predictions[threshold].append(round(probabilities, threshold))

        for label in labels:
            label_to_indices[label].append(i)

    Each iteration appends to a different list, and a comprehension builds one
    list -- so the repair does not exist and the rule was describing code it
    could not fix.  The receiver has to be independent of everything the loop
    rebinds.
    """
    for loop in ctx.loops:
        if not isinstance(loop, ast.For) or loop.orelse or len(loop.body) != 1:
            continue
        call = _sole_append(loop.body[0])
        if call is None:
            continue
        if ctx.read_names(call.func.value) & ctx.assigned_names(loop):
            continue
        # The repair rebinds the receiver, so the unit has to own it.
        # `for item in new_items: shared_queue.append(item.data)` becomes
        # `shared_queue = [...]`, which builds a fresh local and leaves the
        # caller holding the list it passed in, still empty.
        root = _root_name(call.func.value)
        if root is None or root not in _created_names(ctx.node):
            continue
        # And nothing this unit can see may already be in it. `out = [header]`
        # followed by an append loop is not a comprehension in disguise:
        # `out = [x for x in xs]` silently drops the header, so the repair the
        # message names deletes data. Four of the seventy-seven hits on the
        # evaluation corpus were that shape.
        if _starts_non_empty(ast.unparse(call.func.value), ctx):
            continue
        if _reads_the_target(loop, call, root):
            continue
        if _already_appended_before(ctx, loop, root):
            continue
        yield _evidence(
            unit, "append_only_loop", loop, ("C3.S1", "C10.S3"),
            "loop body is a single `.append()`; a comprehension does the same "
            "work without a bound-method lookup and call per item",
            target=ast.unparse(call.func.value),
        )


def _reads_the_target(loop: ast.AST, call: ast.Call, root: str) -> bool:
    """Whether the loop reads the list it is building, other than to append.

        for x in xs:
            if x not in out:
                out.append(x)

    A comprehension can carry a filter, but not one that consults the list
    being built: `out` is empty while the comprehension runs, so the condition
    means something different. The append's own receiver is excluded, since
    that read is the append.
    """
    receiver = {id(n) for n in ast.walk(call.func.value)}
    return any(
        isinstance(n, ast.Name) and n.id == root and isinstance(n.ctx, ast.Load)
        and id(n) not in receiver
        for n in ast.walk(loop)
    )


def _already_appended_before(ctx: UnitContext, loop: ast.AST, root: str) -> bool:
    """Whether an earlier loop in the unit already appended to this list.

        out = []
        for x in a: out.append(x)
        for y in b: out.append(y)     <- `out` is not empty by the time this runs

    The first is a comprehension. The second is `out.extend(b)`, and suggesting
    a comprehension for it would discard everything the first one put there.
    `_starts_non_empty` cannot see this: the binding really is `[]`, and what
    fills it is a statement in between.
    """
    # An enclosing loop is not an earlier one. `ctx.loops` is in source order,
    # so a loop nested inside another has a later line number and its parent
    # looked like a previous loop that had already filled the list -- which
    # silenced the ordinary nested-append shape entirely.
    around = set(map(id, ctx.loops_around(loop)))
    for other in ctx.loops:
        if other is loop:
            return False
        if id(other) in around:
            continue
        if getattr(other, "lineno", 0) >= getattr(loop, "lineno", 0):
            continue
        if any(n is loop for n in ast.walk(other)):
            continue
        for n in ast.walk(other):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr in {"append", "extend"}
                    and _root_name(n.func.value) == root):
                return True
    return False


def _starts_non_empty(receiver: str, ctx: UnitContext) -> bool:
    """Whether the unit is seen binding this receiver to something already in it.

    Only a contradiction counts. `out = []`, `out: list[str] = []` and `list()`
    are all empty starts, and a receiver the unit never binds -- `holder.names`
    on an object it was handed -- says nothing either way, so the rule keeps its
    finding and the reader checks the class. What it must not do is call a list
    that visibly starts with something in it a comprehension in disguise.
    """
    for node in ast.walk(ctx.node):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if not any(ast.unparse(t) == receiver for t in targets):
            continue
        empty = (isinstance(value, ast.List) and not value.elts) or (
            isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
            and value.func.id == "list" and not value.args and not value.keywords
        )
        if not empty:
            return True
    return False


def _root_name(node: ast.AST) -> str | None:
    """`holder.names` -> "holder", `records` -> "records", `buckets[k]` -> None."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _sole_append(statement: ast.stmt) -> ast.Call | None:
    """The `.append()` call a loop body consists of, if that is all it does.

    An `if` around the append counts: `for x in xs: if p(x): out.append(x)` is
    `[x for x in xs if p(x)]`, and skipping it lost the filtered form, which is
    at least as common as the unfiltered one.  Nested `if`s count too, because
    a comprehension takes as many filters as you like -- `if x.valid: if
    x.score > 10:` is `[x for x in xs if x.valid if x.score > 10]`, and
    stripping only one level stopped at the outer one.  An `else` branch does
    not count, because a comprehension has no way to express one.
    """
    while (isinstance(statement, ast.If) and not statement.orelse
           and len(statement.body) == 1):
        statement = statement.body[0]
    if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
        return None
    call = statement.value
    if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
        return call
    return None


def missing_early_exit(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """A search loop that settles its answer but keeps iterating.

    The shape is an `if` whose body only assigns a constant, in a loop with no
    `break` and no `return`.  That alone is nowhere near enough.  The repair is
    to stop the loop early, so the precondition is that stopping early changes
    nothing anyone can see, and five separate ways of failing it were being
    reported:

        status = "OK"
        for server in servers:
            if server.slow:   status = "DEGRADED"
            elif server.down: status = "DOWN"

    A later iteration can overwrite the value with a *different* one.  So the
    loop has to settle exactly one name on exactly one value.

        for event in events:
            if event.kind == "start": seen_start = True
            if event.kind == "end":   seen_end = True

    Two independent flags: stopping at the first would miss the second.

        for row in rows:
            if row.ok: flag = True
            else:      flag = False

    The same name set to a different constant, in a branch the old code never
    looked at -- it read the `if` body and nothing else, so `elif` chains were
    caught and a plain `else` was not.  Now every write to the name anywhere in
    the loop has to agree, whatever construct it sits in.

        for item in items:
            valid = False
            if item.passes_check: valid = True
            send_metric(item, valid)

    The name is re-initialised every pass and consumed every pass, so it is not
    settling anything.  Same check catches it: `valid = False` is another write.

        for item in stream:
            log_event(item)
            stats.total += 1
            if item.is_target: found = True

    And the one that needs a different check.  Nothing writes `found` twice
    here, but the loop is doing work for someone else -- a call out to an
    unknown function, and a counter on an object the caller holds.  Break early
    and both stop happening.  So everything in the loop outside the settling
    `if` has to be invisible from outside: writes to plain local names, and
    calls that are either pure builtins or methods on a name this unit itself
    created.  That last clause is what keeps the true positives:

        while head:
            if head in visited: result = True
            visited.add(head)
            head = head.next

    `visited.add(head)` mutates a set this function made and nobody else can
    reach, and `head = head.next` only advances the search.  Both exist to keep
    the loop going, which is precisely the thing being cut.
    """
    created = _created_names(ctx.node)
    for loop in ctx.loops:
        if _contains_exit(loop):
            continue

        # Only the innermost loop around a settling `if` is asked to stop.  A
        # nested search reported once per level, and the outer loop cannot be
        # left by a `break` written inside the inner one anyway.
        settling = [
            node for node in ast.walk(loop)
            if isinstance(node, ast.If)
            and _assigns_only_constants(node.body)
            and ctx.loops_around(node)[-1:] == (loop,)
        ]
        settled: dict[str, set[str]] = {}
        first: dict[str, ast.AST] = {}
        for node in settling:
            for assignment in node.body:
                for target in assignment.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    settled.setdefault(target.id, set()).add(ast.unparse(assignment.value))
                    first.setdefault(target.id, node)
        if len(settled) != 1:
            continue
        name, values = next(iter(settled.items()))
        if len(values) != 1:
            continue

        # Two exemptions, not one.  A settling `if`'s *body* is the write this
        # rule is reporting, and its *test* is the search being short-circuited.
        # Its `else` is neither: walking the whole `if` node hid `else: flag =
        # False` from the very check written to catch it.
        settling_writes = {
            id(inner) for node in settling
            for statement in node.body for inner in ast.walk(statement)
        }
        settling_exempt = settling_writes | {
            id(inner) for node in settling for inner in ast.walk(node.test)
        }
        if _written_elsewhere(loop, name, settling_writes):
            continue
        if not _work_stays_local(loop, ctx, created, settling_exempt):
            continue

        yield _evidence(
            unit, "missing_early_exit", first[name], ("C3.S5",),
            f"`{name}` is set to its final value and the loop keeps going; no "
            f"`break` or `return` leaves it, and nothing later can change it",
            settled=name,
            loop_line=loop.lineno,
        )


def _contains_exit(loop: ast.AST) -> bool:
    """Whether *this* loop can terminate early.

    The docstring used to say it ignored nested loops' breaks and the code did
    not: `ast.walk` reaches every descendant, so a `break` belonging to an
    inner loop, or a `return` belonging to a `def` written inside the body,
    made the enclosing loop drop out of the analysis entirely.  Neither ends
    this loop.  A `return` in a nested *loop* does, and still counts.
    """

    def scan(node: ast.AST, in_nested_loop: bool) -> bool:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, OPAQUE_NODES + (ast.Lambda,)):
                continue
            if isinstance(child, ast.Return):
                return True
            if isinstance(child, ast.Break) and not in_nested_loop:
                return True
            if scan(child, in_nested_loop or isinstance(child, LOOP_NODES)):
                return True
        return False

    return scan(loop, False)


def _assigns_only_constants(body: list[ast.stmt]) -> bool:
    return bool(body) and all(
        isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Constant)
        for statement in body
    )


def _bound_names(target: ast.AST) -> Iterator[str]:
    """The names one assignment target binds, flattening `a, (b, c) = ...`."""
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _bound_names(element)
    elif isinstance(target, ast.Starred):
        yield from _bound_names(target.value)


def _written_elsewhere(loop: ast.AST, name: str, settling: set[int]) -> bool:
    """Whether the loop writes `name` anywhere but in a settling `if` body.

    Any second write is disqualifying whatever its value: a different constant
    means the loop has not settled, and the same constant reached by another
    route means the shape is not the one this rule can reason about.  The old
    code only read the bodies of `if` statements, which is why `else: flag =
    False` and a plain `valid = False` at the top of the body both slipped
    through.
    """
    for node in ast.walk(loop):
        if id(node) in settling:
            continue
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            targets = [node.target]
        elif isinstance(node, ast.NamedExpr):
            targets = [node.target]
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            if name in node.names:
                return True
            continue
        elif isinstance(node, ast.withitem):
            targets = [node.optional_vars] if node.optional_vars else []
        elif isinstance(node, ast.ExceptHandler):
            if node.name == name:
                return True
            continue
        for target in targets:
            if name in set(_bound_names(target)):
                return True
    return False


# Statements whose effect a `break` would skip, or whose control flow this rule
# is not equipped to reason about.  A whitelist would be nicer, but `ast.walk`
# hands back expressions too, so the check is framed as what disqualifies.
_ESCAPING_STATEMENTS = (
    ast.Yield, ast.YieldFrom, ast.Await, ast.Raise, ast.Try,
    ast.With, ast.AsyncWith, ast.Delete, ast.Global, ast.Nonlocal,
)


def _created_names(scope: ast.AST) -> set[str]:
    """Names this unit binds by assignment, so an object it alone can reach.

    Deliberately not `ctx.assigned_names`, which also returns parameters -- and
    a parameter is the one thing that must not count here.  `audit.record(row)`
    and `visited.add(head)` are the same syntax; what separates them is that
    `visited = set()` appears in the function and `audit` arrived from the
    caller, who can still see what the loop did to it.
    """
    names: set[str] = set()
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(_bound_names(target))
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            names.update(_bound_names(node.target))
        elif isinstance(node, ast.withitem) and node.optional_vars is not None:
            names.update(_bound_names(node.optional_vars))
    return names


def _work_stays_local(loop: ast.AST, ctx: UnitContext, created: set[str],
                      settling: set[int]) -> bool:
    """Whether everything the loop does besides settling the flag is invisible
    outside it.

    Three ways work escapes, and the loop keeps its finding only if it does
    none of them:

    A store into anything but a bare name -- `stats.total += 1`, `cache[k] = v`
    -- reaches an object somebody else is holding.

    A call to a bare name is a function this unit did not define and cannot see
    into, so `log_event(item)` has to be assumed to do something.  Pure
    builtins are the exception, since `len` and `max` are the arithmetic of the
    loop rather than its output.

    A method call is allowed only on a name this unit *created* -- `visited` in
    `visited = set()`.  A method on a parameter, on a loop variable, or on an
    attribute reaches an object from outside, and `audit.record(row)` is the
    same escape as the counter.

    The settling `if` itself is exempt, tests included.  `if not record.check()`
    calls out to something unknown on every pass, and that call *is* the search
    being short-circuited -- charging the rule for it would leave it able to
    report only loops that search nothing.
    """
    iterated = ctx.iteration_names(loop) | {
        n for node in ast.walk(loop)
        if isinstance(node, (ast.For, ast.AsyncFor))
        for n in _bound_names(node.target)
    }
    reachable_only_here = created - iterated

    skip = set(settling)
    if isinstance(loop, (ast.For, ast.AsyncFor)):
        skip.update(id(node) for node in ast.walk(loop.iter))

    for node in ast.walk(loop):
        if id(node) in skip:
            continue
        if isinstance(node, _ESCAPING_STATEMENTS):
            return False
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(not isinstance(target, (ast.Name, ast.Tuple, ast.List))
                   for target in targets):
                return False
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id not in PURE_BUILTINS:
                    return False
            elif isinstance(func, ast.Attribute):
                base = func.value
                if not (isinstance(base, ast.Name) and base.id in reachable_only_here):
                    return False
            else:
                return False
    return True


def try_except_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Exception handling on the per-iteration path.

    Cheap when exceptions are rare, expensive when they are the common case --
    which of the two applies is exactly what the reader has to decide.

    C4.S6 only.  It used to name C3.S3 as well, which is "an object or resource
    created once per iteration that the whole loop could share" -- and a `try`
    creates nothing at all. Entering one is a table lookup at compile time; the
    cost this rule points at is the raise, and the raise is a property of the
    data.
    """
    for node, enclosing in ctx.inside_loops():
        if isinstance(node, ast.Try):
            if not node.handlers:
                # `try/finally` with no `except` catches nothing, so there is
                # no exception path to be on. C4.S6 is an exception used as
                # control flow; this is cleanup, and it has to run.
                continue
            yield _evidence(
                unit, "try_except_in_loop", node, ("C4.S6",),
                "try/except sits on the per-iteration path; if the exception is "
                "the common case, each raise allocates and unwinds",
                loop_line=enclosing[-1].lineno,
                handlers=[ast.unparse(h.type) if h.type else "bare" for h in node.handlers],
            )


def regex_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Regex work repeated per element, where the pattern could be built once.

    Suggests both C3.S3 and C8.S2: hoisting to the enclosing function is the
    former, hoisting to module scope so it survives across calls is the latter.

    Comprehensions count -- `[re.sub(p, "", line) for line in lines]` pays the
    same per-element lookup as the statement loop.  A pattern that depends on
    what is being iterated does not: `[re.compile(p).findall(t) for p in
    patterns]` has nothing to hoist, which is C3.S3's own counter-example.
    """
    for node in ctx.own_nodes():
        if not ctx.repeats(node):
            continue
        found = _regex_call(node, ctx)
        if found is None:
            continue
        label, pattern = found
        # Only the *pattern* has to be invariant. The subject is the element
        # being iterated in every one of these calls, so testing the whole call
        # for a dependency rejected every true positive.
        if ctx.read_names(pattern) & ctx.iteration_names(node):
            continue
        scopes = ctx.repeats_around(node)
        # Nor does a pattern built from it a line earlier: `pattern = "^" +
        # re.escape(key)` inside `for key in fields` is a new pattern each pass.
        if ctx.read_names(pattern) & ctx.assigned_names(scopes[-1]):
            continue
        yield _evidence(
            unit, "regex_in_loop", node, ("C3.S3", "C8.S2"),
            f"`{label}()` is called once per element; the pattern is "
            f"re-resolved every time",
            call=label,
            loop_line=getattr(scopes[-1], "lineno", unit.lineno),
        )


def _regex_call(node: ast.AST, ctx: UnitContext):
    """`(label, pattern)` if this call is a module-level `re` function.

    Three spellings were being missed, all of them ordinary.  `from re import
    search` binds the function directly, so the call is an `ast.Name` and the
    rule only looked at `ast.Attribute`.  `import re as regex` renames the
    module.  And `re.search(pattern=p, string=line)` puts the pattern in a
    keyword, where reading `node.args[0]` finds nothing and the call was
    skipped as if it had no pattern at all.
    """
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute):
        base = func.value
        if not isinstance(base, ast.Name) or func.attr not in RE_FUNCTIONS:
            return None
        if base.id != "re" and ctx.imports.get(base.id) != "re":
            return None
        label = f"{base.id}.{func.attr}"
    elif isinstance(func, ast.Name):
        if func.id not in RE_FUNCTIONS or ctx.imports.get(func.id) != "re":
            return None
        label = func.id
    else:
        return None

    if node.args:
        return label, node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "pattern":
            return label, keyword.value
    return None


MUTATING_METHODS = frozenset({
    "append", "remove", "insert", "pop", "extend", "clear",
    # Reordering skips and repeats elements just as surely as removing one, and
    # a set or dict mutated mid-iteration raises RuntimeError outright.
    "reverse", "sort", "add", "discard", "update", "popitem", "setdefault",
})


def mutation_during_iteration(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Mutating the very collection a `for` loop is walking."""
    for loop in ctx.loops:
        # An attribute is where a collection usually lives, so matching only a
        # bare name missed `for job in self.pending: self.pending.remove(job)`.
        # A call -- `for x in list(xs)` -- is the repair and must stay quiet.
        iterated = _iterated_collection(loop)
        if iterated is None:
            continue
        deferred = _deferred_nodes(loop)
        # The body only. A `for ... else:` block runs after the walk has ended,
        # so appending there is not mutating anything being iterated.
        for node in (n for statement in loop.body for n in ast.walk(statement)):
            if id(node) in deferred:
                continue
            operation = None
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in MUTATING_METHODS
                    and ast.unparse(node.func.value) == iterated):
                operation = f".{node.func.attr}()"
            elif isinstance(node, ast.Delete):
                # `del queue[0]` is an `ast.Delete`, not a call, so a rule
                # looking only for method names walked straight past it.
                for victim in node.targets:
                    if (isinstance(victim, ast.Subscript)
                            and ast.unparse(victim.value) == iterated):
                        operation = "`del`"
                        break
            elif isinstance(node, ast.Assign):
                # `d[k + "_x"] = 1` inserts a key and raises RuntimeError, and
                # a store is neither a call nor a `del`, so it was invisible.
                for victim in node.targets:
                    if _inserts_a_derived_key(victim, iterated, loop.target):
                        operation = "a store under a new key"
                        break
            if operation is None:
                continue
            if _stops_immediately(node, loop):
                continue
            yield _evidence(
                unit, "mutation_during_iteration", node, ("C3.S7",),
                f"`{iterated}` is mutated with {operation} while being "
                f"iterated, which skips elements or grows the loop unboundedly",
                collection=iterated,
                operation=operation.strip("`.()"),
            )


def _iterated_collection(loop: ast.AST) -> str | None:
    """The collection a `for` walks, seeing through `enumerate`.

    `for i, x in enumerate(lst): lst.pop(i)` mutates the thing it is walking
    just as plainly as the bare form, but the iterable is a `Call`, and
    requiring a `Name` or `Attribute` walked straight past it. `reversed` is
    not included: it materialises nothing but does walk a live view, which is
    the same hazard, while `sorted` and a slice both copy and are the repair.
    """
    if not isinstance(loop, ast.For):
        return None
    it = loop.iter
    if (isinstance(it, ast.Call) and isinstance(it.func, ast.Name)
            and it.func.id == "enumerate" and it.args):
        it = it.args[0]
    return ast.unparse(it) if isinstance(it, (ast.Name, ast.Attribute)) else None


def _stops_immediately(node: ast.AST, loop: ast.AST) -> bool:
    """Whether the block holding this mutation ends the loop on the same pass.

        for u in users:
            if u is target:
                users.remove(u)
                break

    Nothing is skipped, because there is no next iteration to skip it. This is
    the ordinary way to remove one element by search, and reporting it told
    correct code it was broken.
    """
    innermost, smallest = None, None
    for parent in ast.walk(loop):
        for attr in ("body", "orelse", "finalbody"):
            block = getattr(parent, attr, None)
            if not isinstance(block, list) or not block:
                continue
            if not any(node is n or node in set(ast.walk(n)) for n in block):
                continue
            # Several blocks contain the node -- the loop's own body, the `if`
            # inside it, and so on. Only the innermost decides, because that is
            # the one whose next statement actually runs.
            size = sum(len(list(ast.walk(n))) for n in block)
            if smallest is None or size < smallest:
                innermost, smallest = block, size
    if innermost is None:
        return False
    return any(isinstance(s, (ast.Break, ast.Return)) for s in innermost)


def _inserts_a_derived_key(target: ast.AST, iterated: str,
                           loop_target: ast.AST) -> bool:
    """Whether this store can add a key to the collection being iterated.

    Three shapes have to come apart, and only the middle one is a bug:

        for k in d: d[k] = f(k)        legal -- the key already exists, so the
                                       dict does not change size
        for k in d: d[k + "_x"] = 1    RuntimeError: dictionary changed size
        for x in xs: xs[0] = x         legal -- storing at a list index never
                                       resizes the list

    So the index has to be *derived from* the loop variable without *being* it.
    Reading the loop variable is what says the collection is keyed by its own
    elements, which is the dict-shaped case; being exactly the loop variable
    says the key is one already present.  An index that never mentions the loop
    variable is left alone, because for a list it is ordinary and for a dict
    this rule cannot tell whether the key is new.
    """
    if not isinstance(target, ast.Subscript):
        return False
    if ast.unparse(target.value) != iterated:
        return False
    if not isinstance(loop_target, ast.Name):
        return False
    index = target.slice
    if isinstance(index, ast.Name) and index.id == loop_target.id:
        return False                    # the key is already in the collection
    return any(isinstance(n, ast.Name) and n.id == loop_target.id
               for n in ast.walk(index))


def _deferred_nodes(loop: ast.AST) -> set[int]:
    """Nodes inside a lambda or a nested `def`, which do not run in this loop.

    `btn.on_delete(lambda: items.remove(item))` registers a callback for some
    later event.  Nothing is mutated during the iteration, and `ast.walk` sees
    no difference between that and a bare `items.remove(item)`.
    """
    found: set[int] = set()
    for node in ast.walk(loop):
        if isinstance(node, (ast.Lambda,) + OPAQUE_NODES):
            found.update(id(inner) for inner in ast.walk(node))
            found.discard(id(node))
    return found


RULES = [
    loop_invariant_expression,
    string_concat_in_loop,
    repeated_lookup_in_loop,
    membership_test_on_sequence,
    index_based_iteration,
    append_only_loop,
    missing_early_exit,
    try_except_in_loop,
    regex_in_loop,
    mutation_during_iteration,
]
