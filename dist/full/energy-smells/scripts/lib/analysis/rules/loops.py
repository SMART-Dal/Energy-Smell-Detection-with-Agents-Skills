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
from ..context import COMPREHENSION_NODES, LOOP_NODES, PURE_METHODS, UnitContext

# C5.S1 puts the break-even for a set at "roughly a dozen elements"; below it,
# scanning a sequence costs less than hashing the thing you are looking for.
SMALL_SEQUENCE = 12

# Functions that compile or parse something reusable.
COMPILE_CALLS = {
    ("re", "compile"), ("re", "search"), ("re", "match"), ("re", "findall"),
    ("re", "sub"), ("re", "fullmatch"), ("re", "split"),
}


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
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
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
        rewritten = ctx.assigned_names(scope) | _mutated_names(scope)
        reported: list[ast.AST] = []
        for node in ctx.per_iteration_nodes(scope):
            if not isinstance(node, REPORTABLE_INVARIANTS):
                continue
            if ctx.repeats_around(node)[-1:] != (scope,):
                continue  # belongs to a nested scope; that scope will report it
            if isinstance(node, ast.Call) and _is_trivial_call(node):
                continue
            if not ctx.is_pure(node):
                continue
            # Only the names the expression reads from *outside* itself matter.
            # A comprehension binds its own targets, and counting those made
            # `{i for i in range(1, k, 2)}` look like it varied with the loop
            # because `i` is assigned somewhere inside it.
            free = ctx.read_names(node) - ctx.assigned_names(node)
            if free & rewritten:
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


def _mutated_names(scope: ast.AST) -> set[str]:
    """Names whose *contents* change inside `scope` without the name being rebound.

    `assigned_names` only sees rebinding, so a work-list traversal
    (`queue.extend(...)` under `while position < len(queue)`) and an in-place
    compaction (`del values[i]` under `while i < len(values)`) both left the
    length looking invariant.  Both are C3.S2 counter-examples where hoisting
    the call is a behaviour change, not an optimisation.
    """
    names: set[str] = set()

    def base(node: ast.AST) -> str | None:
        while isinstance(node, (ast.Subscript, ast.Attribute)):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    for node in ast.walk(scope):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr not in PURE_METHODS:
                names.add(base(node.func.value))
        elif isinstance(node, ast.Delete):
            names.update(base(target) for target in node.targets)
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(base(t) for t in targets
                         if isinstance(t, (ast.Subscript, ast.Attribute)))
    names.discard(None)
    return names


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
        if name not in accumulators and not _looks_stringy(value):
            continue
        if _looks_numeric(value) and name not in accumulators:
            continue

        loop = enclosing[-1]
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
            if _name_is_read_in(loop, target.id, skip=node):
                yield _evidence(
                    unit, "string_concat_in_loop", node, ("C10.S4",),
                    f"`{target.id}` is grown by concatenation inside a loop and "
                    f"is also read there, so a second reference exists and each "
                    f"iteration copies the whole value",
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

    Covers both spellings, because they allocate identically:

        s += x                  AugAssign
        s = s + x               Assign whose value re-reads the target
    """
    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
        return node.target, node.value
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.value, ast.BinOp)
        and isinstance(node.value.op, ast.Add)
    ):
        target = node.targets[0]
        rendered = _target_name(target)
        if _target_name(node.value.left) == rendered:
            return target, node.value.right
        if _target_name(node.value.right) == rendered:
            return target, node.value.left
    return None


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


def _name_is_read_in(loop: ast.AST, name: str, skip: ast.AST | None = None) -> bool:
    """Whether `name` is loaded anywhere in the loop, not just assigned to.

    An augmented assignment stores to its target, so any *load* of the same
    name inside the loop means a second reference is taken -- which is exactly
    what stops CPython from resizing the string in place.

    `skip` excludes the accumulating statement itself, because `s = s + x`
    reads `s` as part of the accumulation.  Counting that as an escaping
    reference would grade every long-form concatenation as aliased.
    """
    skipped = {id(node) for node in ast.walk(skip)} if skip is not None else set()
    return any(
        isinstance(node, ast.Name)
        and node.id == name
        and isinstance(node.ctx, ast.Load)
        and id(node) not in skipped
        for node in ast.walk(loop)
    )


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


MIN_RESOLUTIONS_TO_CACHE = 3
"""Times one attribute chain is walked in a loop before caching it is worth saying.

Raised from two. Resolving `labels.iloc` twice costs two dict lookups against a
local binding the next reader has to carry, which is not a finding -- it is the
shape of ordinary code, and reporting it buried the chains that really are
walked five or six times."""


def repeated_lookup_in_loop(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Attribute chains or globals resolved repeatedly inside a loop body.

    Each `a.b.c` costs a dict lookup per level, and each global costs a scope
    chain walk.  Only chains of depth >= 2 that appear more than once and are
    never rewritten in the loop are reported.

    Chains rooted at an imported module -- `np.searchsorted`, `pd.isna`,
    `math.sqrt` -- are left alone.  `global_lookup_in_loop` already declines to
    tell anyone to bind `np` itself to a local, and it would be incoherent to
    refuse that and then ask for `searchsorted = np.searchsorted` one dot later.
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
    """
    reported_at: dict[int, set[str]] = {}
    for loop in ctx.loops:
        rewritten = ctx.assigned_names(loop)
        rebound = _rebound_chains(loop)
        covered = set().union(
            *(reported_at.get(id(outer), set()) for outer in ctx.loops_around(loop)),
            set(),
        )
        seen: dict[str, list[ast.AST]] = {}
        for node in ast.walk(loop):
            if not isinstance(node, ast.Attribute) or not isinstance(node.ctx, ast.Load):
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
        if not ctx.repeats(node):
            continue
        haystack = node.comparators[0]
        if not _is_sequence_valued(haystack, ctx):
            continue
        if _is_small_sequence(haystack, ctx):
            continue
        enclosing = ctx.repeats_around(node)
        yield _evidence(
            unit, "membership_test_on_sequence", node, ("C5.S1", "C5.S2", "C3.S4"),
            f"membership test `{ast.unparse(node)}` scans a sequence linearly "
            f"on every iteration; a set or dict index would be constant-time",
            haystack=ast.unparse(haystack),
            loop_line=getattr(enclosing[-1], "lineno", unit.lineno),
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


def _annotation_root(node: ast.AST) -> str | None:
    """`list[int]` -> "list", `typing.List[str]` -> "List"."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _annotation_root(node.value)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.split("[")[0].strip().rsplit(".", 1)[-1] or None
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

    Comprehension generators count as well as `for` statements: the index-driven
    form is just as common written as `[grid[i][i] for i in range(len(grid))]`.
    """
    for scope, target, iterable in _iteration_clauses(ctx):
        if not isinstance(target, ast.Name):
            continue
        sequence = _range_len_argument(iterable)
        if sequence is None:
            continue
        index = target.id
        if not any(
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Name)
            and node.slice.id == index
            for node in ast.walk(scope)
        ):
            continue
        yield _evidence(
            unit, "index_based_iteration", scope, ("C3.S1",),
            f"iterating `range(len({sequence}))` and indexing back into it; "
            f"iterating the sequence directly avoids an index lookup per item",
            sequence=sequence,
            index=index,
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
        yield _evidence(
            unit, "append_only_loop", loop, ("C3.S1", "C10.S3"),
            "loop body is a single `.append()`; a comprehension does the same "
            "work without a bound-method lookup and call per item",
            target=ast.unparse(call.func.value),
        )


def _sole_append(statement: ast.stmt) -> ast.Call | None:
    """The `.append()` call a loop body consists of, if that is all it does.

    An `if` around the append counts: `for x in xs: if p(x): out.append(x)` is
    `[x for x in xs if p(x)]`, and skipping it lost the filtered form, which is
    at least as common as the unfiltered one.  An `else` branch does not count,
    because a comprehension has no way to express one.
    """
    if isinstance(statement, ast.If) and not statement.orelse and len(statement.body) == 1:
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
    `break` and no `return`.  That alone is not enough, and two shapes used to
    be reported that are not findings:

        status = "OK"
        for server in servers:
            if server.slow:  status = "DEGRADED"
            elif server.down: status = "DOWN"

    A later iteration can overwrite the value with a *different* one, so
    breaking early changes the answer.  And:

        for event in events:
            if event.kind == "start": seen_start = True
            if event.kind == "end":   seen_end = True

    Two independent flags, so stopping at the first would miss the second.

    So the loop has to settle exactly one name, on exactly one value: once it
    is set, no remaining iteration can change what the loop returns.
    """
    for loop in ctx.loops:
        if _contains_exit(loop):
            continue
        settled: dict[str, set[str]] = {}
        first: dict[str, ast.AST] = {}
        for node in ast.walk(loop):
            if not (isinstance(node, ast.If) and _assigns_only_constants(node.body)):
                continue
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
        yield _evidence(
            unit, "missing_early_exit", first[name], ("C3.S5",),
            f"`{name}` is set to its final value and the loop keeps going; no "
            f"`break` or `return` leaves it, and nothing later can change it",
            settled=name,
            loop_line=loop.lineno,
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
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        base = node.func.value
        if not isinstance(base, ast.Name):
            continue
        if (base.id, node.func.attr) not in COMPILE_CALLS:
            continue
        scopes = ctx.repeats_around(node)
        # Only the *pattern* has to be invariant. The subject is the element
        # being iterated in every one of these calls, so testing the whole call
        # for a dependency rejected every true positive.
        pattern = node.args[0] if node.args else None
        if pattern is None or ctx.read_names(pattern) & ctx.iteration_names(node):
            continue
        yield _evidence(
            unit, "regex_in_loop", node, ("C3.S3", "C8.S2"),
            f"`{base.id}.{node.func.attr}()` is called once per element; the "
            f"pattern is re-resolved every time",
            call=f"{base.id}.{node.func.attr}",
            loop_line=getattr(scopes[-1], "lineno", unit.lineno),
        )


def mutation_during_iteration(unit: UnitRef, ctx: UnitContext) -> Iterator[Evidence]:
    """Mutating the very collection a `for` loop is walking."""
    for loop in ctx.loops:
        # An attribute is where a collection usually lives, so matching only a
        # bare name missed `for job in self.pending: self.pending.remove(job)`.
        # A call -- `for x in list(xs)` -- is the repair and must stay quiet.
        if not isinstance(loop, ast.For) or not isinstance(loop.iter, (ast.Name, ast.Attribute)):
            continue
        iterated = ast.unparse(loop.iter)
        for node in ast.walk(loop):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"append", "remove", "insert", "pop", "extend", "clear"}:
                continue
            if ast.unparse(node.func.value) != iterated:
                continue
            yield _evidence(
                unit, "mutation_during_iteration", node, ("C3.S7",),
                f"`{iterated}` is mutated with `.{node.func.attr}()` while being "
                f"iterated, which skips elements or grows the loop unboundedly",
                collection=iterated,
                operation=node.func.attr,
            )


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
