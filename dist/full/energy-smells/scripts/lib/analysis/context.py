"""Facts about a unit that many analyzers need, computed once.

Without this, every analyzer would re-walk the tree to answer the same three
questions: what encloses this node, which names does this loop rewrite, and is
this call safe to move.  Computing them once keeps the analyzers themselves
short enough to read in one sitting.

The analyses here are deliberately *approximate but conservative*: when we
cannot prove something is safe, we say it is not.  A missed smell costs recall;
a wrongly-hoisted call would make the tool propose a patch that changes
behaviour, which is far worse.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from functools import cached_property

LOOP_NODES = (ast.For, ast.AsyncFor, ast.While)
COMPREHENSION_NODES = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)

# Definitions whose contents belong to a unit of their own, so the context of
# an enclosing function must not reach into them.
OPAQUE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

# Builtins with no side effects, safe to hoist out of a loop or deduplicate.
# Anything absent from this set is treated as impure.
PURE_BUILTINS = frozenset({
    "abs", "all", "any", "ascii", "bin", "bool", "bytes", "callable", "chr",
    "complex", "dict", "divmod", "float", "format", "frozenset", "hash", "hex",
    "int", "isinstance", "issubclass", "len", "list", "max", "min", "oct",
    "ord", "pow", "repr", "round", "set", "sorted", "str", "sum", "tuple",
    "zip", "range", "enumerate", "reversed", "map", "filter",
})

# Builtins that are pure but hand back a one-shot iterator.  Safe to call,
# never safe to *reuse*: hoisting one out of a loop or binding it to a name and
# reading it twice leaves every pass after the first with an exhausted object.
LAZY_BUILTINS = frozenset({"zip", "map", "filter", "enumerate", "reversed", "iter"})

# String/collection methods that only read their receiver.
#
# `get` is deliberately absent.  These names are matched on the attribute alone,
# because the receiver's type is not knowable here, and `.get` is the one that
# collides with something destructive: `queue.get()` and `channel.get()` remove
# an item, and a rule told they were pure offered to hoist a channel receive out
# of the loop that drains it.  The others collide too, which is what
# `module_aliases` below is for -- `shutil.copy` and `requests.get` are the
# module-level spellings of the same mistake.  Losing `dict.get` costs one
# recognised shape; keeping it recommended a deadlock.
PURE_METHODS = frozenset({
    "count", "index", "find", "rfind", "startswith", "endswith", "lower",
    "upper", "strip", "lstrip", "rstrip", "split", "rsplit", "join",
    "replace", "format", "encode", "decode", "keys", "values",
    "items", "copy", "isdigit", "isalpha", "isspace", "title", "capitalize",
})

# Modules whose presence means array/native code, where hardware locality
# smells (C12) become worth probing and vectorisation (C10.S3) applies.
ARRAY_MODULES = frozenset({"numpy", "np", "pandas", "pd", "torch", "scipy", "array"})

CHEAP_BUILTIN_CALLS = frozenset({
    "len", "int", "float", "bool", "str", "abs", "round", "ord", "chr",
    "isinstance", "issubclass", "type", "id", "hasattr", "getattr", "callable",
    "range", "enumerate", "zip", "reversed", "iter",
})
"""Builtins that cost one call and no pass over their argument.

`range`, `enumerate`, `zip`, `reversed` and `iter` build a lazy object; the
rest read a field or convert a scalar. `min` and `max` join them only when
given separate arguments -- `max(n, 1)` -- since over one iterable they walk it."""

LOOKUP_METHODS = frozenset({"get"})
"""A method that is one dict probe: the cost of a subscript.

Not `keys`, `values` or `items`, though building a view is as cheap: `key in
mapping.keys()` inside a loop is the C4.S8 shape, measured at 35-55%, and on
the AST arm the loop-invariant report is what points at it."""


def is_cheap_expression(node: ast.AST) -> bool:
    """Whether evaluating this costs a lookup or a call and nothing more.

    `len(x)`, `float(config["min_score"])`, `markers[arm]`, `float("nan")`,
    `max(n_total, 1)`, `prim_h - 0.66`, `{"left": LEFT, "right": RIGHT}`: the
    handful of operations every Python program is made of. Removing one --
    hoisting it, deleting it -- saves about what the one-dot lookup
    `C8S3_bound_method_alias` saved, 10.6% in a loop doing nothing else, and
    inside the 15% the scan treats as no effect. Rules use this to stay quiet
    where the measured shapes of their root causes did real work: a `sorted()`,
    a comprehension, a call into the program's own code.

    Not cheap: a slice (`x[1:]` copies), a comprehension, any other call, and a
    list or tuple repeated (`[0] * n` allocates n slots).
    """
    if isinstance(node, (ast.Constant, ast.Name)):
        return True
    if isinstance(node, ast.Attribute):
        return is_cheap_expression(node.value)
    if isinstance(node, ast.Subscript):
        return (not isinstance(node.slice, ast.Slice)
                and is_cheap_expression(node.value) and is_cheap_expression(node.slice))
    if isinstance(node, ast.UnaryOp):
        return is_cheap_expression(node.operand)
    if isinstance(node, ast.BinOp):
        repeats = isinstance(node.op, ast.Mult) and any(
            isinstance(side, (ast.List, ast.Tuple)) for side in (node.left, node.right))
        return (not repeats and is_cheap_expression(node.left)
                and is_cheap_expression(node.right))
    if isinstance(node, ast.IfExp):
        return all(is_cheap_expression(part) for part in (node.test, node.body, node.orelse))
    if isinstance(node, (ast.Compare, ast.BoolOp)):
        parts = ([node.left, *node.comparators] if isinstance(node, ast.Compare)
                 else node.values)
        return all(is_cheap_expression(part) for part in parts)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(is_cheap_expression(element) for element in node.elts)
    if isinstance(node, ast.Dict):
        return all(is_cheap_expression(part)
                   for part in (*node.keys, *node.values) if part is not None)
    if isinstance(node, ast.JoinedStr):
        return all(is_cheap_expression(part.value) if isinstance(part, ast.FormattedValue)
                   else True for part in node.values)
    if isinstance(node, ast.Call):
        if any(isinstance(argument, ast.Starred) for argument in node.args):
            return False
        func = node.func
        if isinstance(func, ast.Name):
            cheap_callee = (func.id in CHEAP_BUILTIN_CALLS
                            or (func.id in {"min", "max"} and len(node.args) >= 2))
        elif isinstance(func, ast.Attribute):
            cheap_callee = func.attr in LOOKUP_METHODS and is_cheap_expression(func.value)
        else:
            cheap_callee = False
        return cheap_callee and all(
            is_cheap_expression(argument)
            for argument in (*node.args, *(k.value for k in node.keywords))
        )
    return False


@dataclass
class UnitContext:
    """Precomputed structure and safety facts for one unit."""

    node: ast.AST
    source: str
    imports: dict[str, str] = field(default_factory=dict)
    """Bound name -> module it came from, e.g. {"np": "numpy"}."""

    module_aliases: frozenset[str] = frozenset()
    """Names bound to a module itself, e.g. `np` from `import numpy as np`.

    Distinct from `imports`, which cannot tell them apart: `import numpy as np`
    and `from numpy import array` both record "numpy" as the source. The
    difference matters where the advice is to bind a name to a local -- nobody
    writes `_np = np`, while binding an imported function is ordinary code."""

    module_bindings: dict[str, ast.AST] = field(default_factory=dict)
    """Module-level constant -> its assigned value, for names the unit only reads."""

    overridden_methods: frozenset[str] = frozenset()

    entry_depth: int = 0
    """Loops this unit is already inside before it runs a line of its own.

    Filled from the call graph by `engine._apply_rules`, and only on a
    whole-tree scan with cross-unit analysis switched on. Zero otherwise, which
    is what makes every rule that ignores it behave exactly as it did when a
    unit was the whole world.

    A unit whose body has no loop at all can still be the hottest thing in a
    repo. `def check(x): return x in ALLOWED` is straight-line code until you
    see that its one caller is a doubly-nested loop in another file, at which
    point the linear scan inside it runs n*m times. That fact lives in the
    edge, not in either function, so no amount of reading one file finds it.
    """
    """Method names that take part in an override relationship in this module.

    A method that never touches `self` is a static-declaration candidate right
    up until a subclass overrides it, at which point the call site is a dispatch
    point and pinning it to a class silently skips the override. That fact lives
    one level above the unit, so it has to be collected from the module and
    handed down."""

    def __post_init__(self) -> None:
        self._parents: dict[ast.AST, ast.AST] = {}
        self._repeat_stack: dict[ast.AST, tuple[ast.AST, ...]] = {}
        self._assigned: dict[ast.AST, frozenset[str]] = {}
        self._own: tuple[ast.AST, ...] | None = None
        self._index()

    # -- structure ---------------------------------------------------------

    def _index(self) -> None:
        """Walk the unit once, recording parents and what repeats around each node.

        Two things this walk deliberately does:

        It records loops and comprehensions in one stack, in the order they
        nest, so a rule can ask for either.  `for x in xs: [f(y) for y in ys]`
        is doubly repeated and a rule that only knew about statement loops
        could not see it.

        And it stops at a nested definition.  `iter_units` emits an inner
        function as a unit of its own with its own context, so descending into
        one here made every enclosing function report the inner function's
        findings a second time -- against a unit where the reader cannot act on
        them.  The definition *statement* still belongs to this unit and keeps
        its place in the stack -- a `def` written inside a loop builds a new
        function object on every pass -- only its body is handed over.

        The stack a node gets is relative to the scope it runs in, which is why
        a loop's iterable is not counted as being inside that loop.  Reading it
        straight off the nesting made `for q in neighbors(p)` inside another
        loop report depth 2, when `neighbors` runs once per `p`, and that number
        is the first term of every unit's ranking.
        """

        def walk(node: ast.AST, repeats: tuple[ast.AST, ...], once: ast.AST | None) -> None:
            if isinstance(node, (ast.For, ast.AsyncFor)):
                once = node.iter
            elif isinstance(node, COMPREHENSION_NODES) and node.generators:
                once = node.generators[0].iter
            for child in ast.iter_child_nodes(node):
                if isinstance(child, OPAQUE_NODES):
                    self._parents[child] = node
                    self._repeat_stack[child] = repeats
                    continue
                self._parents[child] = node
                # The clause a loop draws from runs before the loop starts, so
                # it repeats as often as whatever encloses *that loop*, not as
                # often as the loop's own body.  `repeats[-1]` is the loop we
                # are inside, and dropping it is what makes the count relative
                # to the enclosing scope.
                stack = repeats[:-1] if child is once else repeats
                self._repeat_stack[child] = stack
                inner = (
                    stack + (child,)
                    if isinstance(child, LOOP_NODES + COMPREHENSION_NODES)
                    else stack
                )
                walk(child, inner, once)

        self._repeat_stack[self.node] = ()
        walk(self.node, (), None)

    def owns(self, node: ast.AST) -> bool:
        """Whether this node belongs to this unit rather than to a nested one."""
        return node is self.node or node in self._repeat_stack

    def own_nodes(self):
        """Every node this unit is responsible for, nested definitions excluded.

        Walked once and kept: most rules start from this, and each one walking
        the unit afresh was a large share of a scan's running time.
        """
        if self._own is None:
            self._own = tuple(node for node in ast.walk(self.node) if self.owns(node))
        return iter(self._own)

    def parent_of(self, node: ast.AST) -> ast.AST | None:
        return self._parents.get(node)

    def repeats_around(self, node: ast.AST) -> tuple[ast.AST, ...]:
        """Enclosing loops *and* comprehensions, outermost first."""
        return self._repeat_stack.get(node, ())

    def repeat_depth(self, node: ast.AST) -> int:
        """How many loops and comprehensions this node is nested inside."""
        return len(self.repeats_around(node))

    def loops_around(self, node: ast.AST) -> tuple[ast.AST, ...]:
        """Enclosing `for`/`while` statements, outermost first."""
        return tuple(
            scope for scope in self.repeats_around(node)
            if isinstance(scope, LOOP_NODES)
        )

    def loop_depth(self, node: ast.AST) -> int:
        return len(self.loops_around(node))

    def in_loop(self, node: ast.AST) -> bool:
        return bool(self.loops_around(node))

    def in_comprehension(self, node: ast.AST) -> bool:
        """Whether this node sits inside a comprehension or generator expression."""
        return any(
            isinstance(scope, COMPREHENSION_NODES)
            for scope in self.repeats_around(node)
        )

    def iteration_names(self, node: ast.AST) -> set[str]:
        """Names bound by the loops and comprehensions enclosing `node`.

        An expression that reads one of these changes with every element, so it
        is neither hoistable nor a duplicate of something shared -- which is
        what separates `dict(defaults)` in a loop from `dict(row)`.
        """
        names: set[str] = set()
        for scope in self.repeats_around(node):
            targets = []
            if isinstance(scope, LOOP_NODES):
                targets.append(getattr(scope, "target", None))
            elif isinstance(scope, COMPREHENSION_NODES):
                targets.extend(generator.target for generator in scope.generators)
            for target in targets:
                if target is None:
                    continue
                names.update(
                    inner.id for inner in ast.walk(target) if isinstance(inner, ast.Name)
                )
        return names

    @cached_property
    def repeat_scopes(self) -> list[ast.AST]:
        """Every loop and comprehension in this unit, in source order."""
        return [
            node for node in self.own_nodes()
            if isinstance(node, LOOP_NODES + COMPREHENSION_NODES)
        ]

    def runs_repeatedly(self, node: ast.AST) -> bool:
        """Whether this node runs many times -- counting the callers' loops.

        `repeats` asks about loops written in this unit. This asks the question
        a cost actually depends on, which is how often the line runs, and a
        caller's loop makes a straight-line body run just as often as a local
        one would.

        The repair usually differs even though the finding is the same, because
        there is no local loop to hoist out of, so a rule using this must say
        where the loop it is talking about lives. `entry_depth` is zero unless
        a whole-tree scan turned cross-unit analysis on, so this collapses to
        `repeats` in every other case.
        """
        return self.repeats(node) or self.entry_depth > 0

    def repeats(self, node: ast.AST) -> bool:
        """Whether this node is evaluated once per element of something.

        `in_loop` answers a narrower question -- is there a `for` or `while`
        statement above this -- and rules about per-element cost kept reaching
        for it, which made every one of them blind to comprehensions.  That is
        not a small gap: a comprehension is the commonest way to write a loop in
        Python, and it is what most of this taxonomy's own examples use.
        `[n * 3.0 for n in counts]` is the measured example on C5.S3's card and
        no rule keyed on `in_loop` could see it.

        The clause a loop draws from is excluded, because it runs exactly once:
        `for i in range(len(xs))` does not recompute `len(xs)` per iteration,
        and neither does the outermost `for ... in expensive()` of a
        comprehension.  `_index` has already taken that loop out of the clause's
        stack, so the exclusion is per scope: a *nested* loop's iterable still
        repeats, once for every pass of the loop outside it, and saying
        otherwise made `for q in neighbors(p)` inside another loop answer "no"
        to a question whose true answer is "len(points) times".
        """
        return self.in_loop(node) or self.in_comprehension(node)

    @cached_property
    def loops(self) -> list[ast.AST]:
        """Every `for`/`while` in this unit, in source order."""
        return [n for n in self.own_nodes() if isinstance(n, LOOP_NODES)]

    def inside_loops(self):
        """Yield `(node, enclosing_loops)` for every node that runs in a loop.

        Use this rather than walking each loop in turn.  Walking loops nests:
        a statement inside three loops appears in all three walks, so a rule
        written that way reports the same line three times, which inflates the
        unit's ranking and reads as three separate observations in the report.

        Nodes come out in source order, once each, with their loops outermost
        first -- so `loops[-1]` is the innermost and `len(loops)` is the depth.
        """
        for node in self.own_nodes():
            enclosing = self.loops_around(node)
            if enclosing:
                yield node, enclosing

    @cached_property
    def max_loop_depth(self) -> int:
        """Deepest `for`/`while` nesting: 0 if loop-free, 1 for a flat loop.

        Statement loops only.  Rules that hoist work out of a loop need a
        statement to hoist it above, so this is the number they want; anything
        ranking a unit by how often its lines run wants `max_repeat_depth`.
        """
        return max((self.loop_depth(n) + 1 for n in self.loops), default=0)

    @cached_property
    def max_repeat_depth(self) -> int:
        """Deepest nesting of anything that repeats, comprehensions included.

        `[[f(x, y) for y in ys] for x in xs]` runs `f` len(xs)*len(ys) times
        exactly as the two `for` statements would, so a unit written that way
        is not cold and must not be ranked as though it were.  Counting only
        statement loops made every comprehension-heavy unit report depth 0.
        """
        return max(
            (self.repeat_depth(n) + 1 for n in self.repeat_scopes), default=0
        )

    @cached_property
    def annotation_nodes(self) -> frozenset[int]:
        """`id()` of every node standing in an annotation position.

        `batch: List[Order] = []` inside a loop looks exactly like repeated
        subscript work, and it is none: PEP 526 says a function-local
        annotation is *never* evaluated, whatever its target, so `List[Order]`
        there costs nothing at all.  Measured on the real thing rather than
        read off the PEP -- a class whose `__class_getitem__` prints stays
        silent through three passes of a loop in a function, and prints three
        times when the same loop is at module level.

        So annotations are not uniformly free, and this does not claim they
        are.  It claims something weaker that covers both cases: where they are
        free there is nothing to report, and where they are not, the repair a
        rule would propose is "hoist your type annotation into a local", which
        nobody is going to do.  Either way the honest output is silence.

        Only the annotation is skipped.  `AnnAssign.value` is ordinary code and
        stays visible -- the `[]` in that example is still a fresh list per
        pass, and a rule that cares about allocation should say so.
        """
        found: set[int] = set()
        for node in ast.walk(self.node):
            if isinstance(node, ast.AnnAssign):
                roots = [node.annotation]
            elif isinstance(node, ast.arg):
                roots = [node.annotation] if node.annotation is not None else []
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                roots = [node.returns] if node.returns is not None else []
            else:
                continue
            for root in roots:
                found.update(id(inner) for inner in ast.walk(root))
        return frozenset(found)

    def per_iteration_nodes(self, scope: ast.AST):
        """Yield the nodes of `scope` that are re-evaluated on every iteration.

        A `for` loop's iterable is evaluated exactly once, when the loop starts,
        so `for i in range(len(xs))` does *not* recompute `len(xs)` per
        iteration.  Treating it as loop-invariant work would be simply wrong.
        A `while` loop's test, by contrast, does run every time.

        A comprehension works the same way and is accepted here for the same
        reason: only its *first* generator's iterable is evaluated once, since
        every later one is re-evaluated per element of the one before it.

        The skip is per scope rather than unit-wide.  A nested loop's own
        iterable runs once per iteration of the loop outside it, so it is
        genuinely repeated work as far as that outer loop is concerned.

        Annotations are dropped here too, for the stronger reason that they are
        not re-evaluated per iteration at all.  See `annotation_nodes`.
        """
        if isinstance(scope, (ast.For, ast.AsyncFor)):
            skip = {id(scope.iter)}
        elif isinstance(scope, COMPREHENSION_NODES) and scope.generators:
            skip = {id(scope.generators[0].iter)}
        else:
            skip = set()
        annotations = self.annotation_nodes
        for node in ast.walk(scope):
            if id(node) in skip or id(node) in annotations:
                continue
            if any(id(ancestor) in skip for ancestor in self._ancestors(node)):
                continue
            yield node

    def _ancestors(self, node: ast.AST):
        current = self._parents.get(node)
        while current is not None:
            yield current
            current = self._parents.get(current)

    @cached_property
    def uses_arrays(self) -> bool:
        """Whether the unit's *file* imports a NumPy-like library.

        Gates the hardware-locality analyzers: in pure CPython those effects are
        buried under interpreter dispatch, so probing for them elsewhere would
        only produce noise.

        File-level on purpose, and the name overstates it.  A unit that never
        names an import can still be handed an array -- `def rows(frame)` is the
        ordinary way a helper receives one -- so asking which names *this* unit
        reads would answer no for most of the code that actually touches them.
        The file's imports are the weaker claim that survives that, and the gate
        only decides whether a probe is worth running.
        """
        roots = {module.split(".")[0] for module in self.imports.values()}
        return bool(roots & ARRAY_MODULES) or bool(set(self.imports) & ARRAY_MODULES)

    # -- names -------------------------------------------------------------

    def assigned_names(self, scope: ast.AST) -> set[str]:
        """Every name bound anywhere inside `scope`.

        Covers assignment, augmented assignment, `for` targets, `with ... as`,
        walrus, comprehension targets, imports and nested definitions -- any of
        which makes a name unsafe to treat as constant within that scope.

        A `lambda`'s parameters count too.  They are bound afresh on every call,
        so nothing that reads one is constant across a loop -- and because a
        lambda is not a unit of its own, its body is walked as part of the
        enclosing function, where its parameters would otherwise look like free
        names.  `max(rows, key=lambda x: x[1])` was reported as recomputing a
        loop-invariant `x[1]` on exactly that mistake.

        The binding forms that are *not* `ast.Name` nodes need naming one by
        one, because the walk cannot see them: `except E as e` and `match`
        captures both carry their name as a bare string on the node.  Missing
        the first of those reported `str(e)` inside an `except` clause as
        loop-invariant, when `e` is rebound by every iteration that raises.
        """
        # Rules ask this of the same loop once per node inside it, and the walk
        # is the whole loop, so it is remembered per scope. A copy goes out
        # because callers extend what they get back.
        cached = self._assigned.get(scope)
        if cached is None:
            cached = self._assigned[scope] = frozenset(self._assigned_names(scope))
        return set(cached)

    @staticmethod
    def _assigned_names(scope: ast.AST) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(scope):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                names.add(node.id)
            elif isinstance(node, ast.Lambda):
                names.update(_parameter_names(node))
            elif isinstance(node, ast.ExceptHandler) and node.name:
                names.add(node.name)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                names.update(node.names)
            elif isinstance(node, ast.MatchAs) and node.name:
                names.add(node.name)
            elif isinstance(node, ast.MatchStar) and node.name:
                names.add(node.name)
            elif isinstance(node, ast.MatchMapping) and node.rest:
                names.add(node.rest)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
                names.update(_parameter_names(node))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    names.add(alias.asname or alias.name.split(".")[0])
        return names

    def read_names(self, node: ast.AST) -> set[str]:
        """Every name read inside `node`."""
        return {
            n.id
            for n in ast.walk(node)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }

    # -- safety ------------------------------------------------------------

    def is_pure(self, node: ast.AST) -> bool:
        """Whether evaluating `node` is free of observable side effects.

        Conservative by construction: only calls we positively recognise as
        pure are allowed, everything else disqualifies the expression.  This
        gates hoisting (C3.S2), deduplication (C1.S4) and memoization (C8.S1),
        all of which are unsafe on an impure expression.

        Purity in the mathematical sense is not the question those three ask.
        `zip(keys, values)` has no side effect at all and is still ruinous to
        hoist, because the object it returns is consumed by the first iteration
        and empty for every one after it.  So an expression that *is* a one-shot
        iterator is refused, while one that merely contains it is not:
        `list(zip(a, b))` materialises, and moving it is safe.
        """
        if self.yields_one_shot_iterator(node):
            return False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and not self._is_pure_call(sub):
                return False
            if isinstance(sub, (ast.Await, ast.Yield, ast.YieldFrom, ast.NamedExpr)):
                return False
        return True

    def yields_one_shot_iterator(self, node: ast.AST) -> bool:
        """Whether evaluating this hands back an iterator that empties as it is read."""
        if isinstance(node, ast.GeneratorExp):
            return True
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in LAZY_BUILTINS
        )

    def _is_pure_call(self, call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in PURE_BUILTINS
        if isinstance(func, ast.Attribute):
            # A method is recognised by its name alone, so a module-level
            # function that happens to share one is not recognised at all:
            # `shutil.copy` writes a file and `requests.get` makes a request,
            # and both were being called pure on the strength of `copy` and
            # `get` appearing in the set above.  A module alias is the one
            # receiver whose type *is* readable here, so it is the one case
            # that can be ruled out rather than guessed at.
            if isinstance(func.value, ast.Name) and func.value.id in self.module_aliases:
                return False
            return func.attr in PURE_METHODS
        return False


def collect_imports(tree: ast.Module) -> dict[str, str]:
    """Map every imported binding in a module to its source module."""
    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports[alias.asname or alias.name] = node.module
    return imports


def collect_module_aliases(tree: ast.Module) -> frozenset[str]:
    """Names a plain `import` binds, which stand for modules rather than values."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return frozenset(names)


def collect_overridden_methods(tree: ast.Module) -> frozenset[str]:
    """Method names defined by a class and also by another class that names it
    as a base, in either direction.

    Both ends are returned, because both ends matter: the base's method is the
    one that must stay dispatchable, and the override is the one that proves it.
    Only bases written as a bare name are followed -- `class B(mod.A)` is a
    class this module cannot see, so nothing is claimed about it.

    The whole chain is followed, not just the class's own bases.  `class C(B)`
    where `B` is empty and `A` declares `run` is still an override of `A.run`,
    and pairing only direct bases missed it -- which matters in the direction
    that costs precision, since this set exists to *silence* a rule.  A missed
    override means proposing `@staticmethod` on the base and breaking dispatch.

    Deliberately shallow in the other direction. It does not resolve imported
    bases, inheritance chains through other modules, or `setattr`, so it is a way
    to be quiet about a visible override rather than a promise that no override
    exists, so a rule using it is guessing and should say so in its message.
    """
    methods: dict[str, set[str]] = {}
    bases: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods[node.name] = {
            child.name for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        bases[node.name] = [b.id for b in node.bases if isinstance(b, ast.Name)]

    def ancestors(name: str) -> set[str]:
        seen: set[str] = set()
        pending = list(bases.get(name, ()))
        while pending:
            parent = pending.pop()
            if parent in seen or parent not in methods:
                continue
            seen.add(parent)
            pending.extend(bases.get(parent, ()))
        return seen

    shared: set[str] = set()
    for name in bases:
        for parent in ancestors(name):
            shared |= methods[name] & methods[parent]
    return frozenset(shared)


def collect_module_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    """Map each module-level constant to the value assigned to it.

    A rule that can only see assignments inside its own unit cannot judge
    `if name in ALLOWED` when `ALLOWED` is the module constant above it, which
    is where such tables usually live.  Only names assigned exactly once are
    kept: a name the module rebinds has no settled value to reason from.

    An annotated constant counts.  `ALLOWED: list[str] = [...]` is an `AnnAssign`
    and reading only plain assignments made every module constant in a typed
    file invisible, which is most of them in code written this decade.

    `COUNTER += 1` counts as a rebinding but not as a binding: it proves the
    name does not stay put, and its value is not readable from the statement.
    Ignoring it left the first assignment in the table looking settled, so a
    rule would have reasoned from a value the module had already changed.
    """
    bindings: dict[str, ast.AST] = {}
    rebound: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        elif isinstance(node, ast.AugAssign):
            targets, value = [node.target], None
        else:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if value is None or target.id in bindings:
                rebound.add(target.id)
            if value is not None:
                bindings[target.id] = value
    return {name: value for name, value in bindings.items() if name not in rebound}


def _parameter_names(node: ast.AST) -> set[str]:
    """Parameter names of a `def` or `lambda`, including `*args` and `**kwargs`."""
    args = getattr(node, "args", None)
    if args is None:
        return set()
    names = {
        a.arg for a in (
            *getattr(args, "posonlyargs", []), *args.args, *args.kwonlyargs
        )
    }
    for extra in (args.vararg, args.kwarg):
        if extra is not None:
            names.add(extra.arg)
    return names
