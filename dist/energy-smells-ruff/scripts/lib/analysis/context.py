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

# String/collection methods that only read their receiver.
PURE_METHODS = frozenset({
    "count", "index", "find", "rfind", "startswith", "endswith", "lower",
    "upper", "strip", "lstrip", "rstrip", "split", "rsplit", "join",
    "replace", "format", "encode", "decode", "get", "keys", "values",
    "items", "copy", "isdigit", "isalpha", "isspace", "title", "capitalize",
})

# Modules whose presence means array/native code, where hardware locality
# smells (C12) become worth probing and vectorisation (C10.S3) applies.
ARRAY_MODULES = frozenset({"numpy", "np", "pandas", "pd", "torch", "scipy", "array"})


@dataclass
class UnitContext:
    """Precomputed structure and safety facts for one unit."""

    node: ast.AST
    source: str
    imports: dict[str, str] = field(default_factory=dict)
    """Bound name -> module it came from, e.g. {"np": "numpy"}."""

    def __post_init__(self) -> None:
        self._parents: dict[ast.AST, ast.AST] = {}
        self._repeat_stack: dict[ast.AST, tuple[ast.AST, ...]] = {}
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
        them.
        """

        def walk(node: ast.AST, repeats: tuple[ast.AST, ...]) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, OPAQUE_NODES):
                    self._parents[child] = node
                    continue
                self._parents[child] = node
                self._repeat_stack[child] = repeats
                inner = (
                    repeats + (child,)
                    if isinstance(child, LOOP_NODES + COMPREHENSION_NODES)
                    else repeats
                )
                walk(child, inner)

        self._repeat_stack[self.node] = ()
        walk(self.node, ())

    def owns(self, node: ast.AST) -> bool:
        """Whether this node belongs to this unit rather than to a nested one."""
        return node is self.node or node in self._repeat_stack

    def own_nodes(self):
        """Every node this unit is responsible for, nested definitions excluded."""
        return (node for node in ast.walk(self.node) if self.owns(node))

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
        comprehension.
        """
        if id(node) in self._evaluated_once:
            return False
        return self.in_loop(node) or self.in_comprehension(node)

    @cached_property
    def _evaluated_once(self) -> set[int]:
        """Nodes in an iterable clause, which is evaluated before iteration starts."""
        once: set[int] = set()
        for node in self.own_nodes():
            sources = []
            if isinstance(node, (ast.For, ast.AsyncFor)):
                sources.append(node.iter)
            elif isinstance(node, COMPREHENSION_NODES) and node.generators:
                sources.append(node.generators[0].iter)
            for source in sources:
                once.update(id(inner) for inner in ast.walk(source))
        return once

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
        """Deepest loop nesting in the unit: 0 if loop-free, 1 for a flat loop."""
        return max((self.loop_depth(n) + 1 for n in self.loops), default=0)

    def per_iteration_nodes(self, loop: ast.AST):
        """Yield the nodes of `loop` that are re-evaluated on every iteration.

        A `for` loop's iterable is evaluated exactly once, when the loop starts,
        so `for i in range(len(xs))` does *not* recompute `len(xs)` per
        iteration.  Treating it as loop-invariant work would be simply wrong.
        A `while` loop's test, by contrast, does run every time.
        """
        skip = {id(loop.iter)} if isinstance(loop, (ast.For, ast.AsyncFor)) else set()
        for node in ast.walk(loop):
            if id(node) in skip:
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
        """Whether the unit touches NumPy-like libraries.

        Gates the hardware-locality analyzers: in pure CPython those effects are
        buried under interpreter dispatch, so probing for them elsewhere would
        only produce noise.
        """
        roots = {module.split(".")[0] for module in self.imports.values()}
        return bool(roots & ARRAY_MODULES) or bool(set(self.imports) & ARRAY_MODULES)

    # -- names -------------------------------------------------------------

    def assigned_names(self, scope: ast.AST) -> set[str]:
        """Every name bound anywhere inside `scope`.

        Covers assignment, augmented assignment, `for` targets, `with ... as`,
        walrus, comprehension targets, imports and nested definitions -- any of
        which makes a name unsafe to treat as constant within that scope.
        """
        names: set[str] = set()
        for node in ast.walk(scope):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                names.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
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
        """
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and not self._is_pure_call(sub):
                return False
            if isinstance(sub, (ast.Await, ast.Yield, ast.YieldFrom, ast.NamedExpr)):
                return False
        return True

    def _is_pure_call(self, call: ast.Call) -> bool:
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in PURE_BUILTINS
        if isinstance(func, ast.Attribute):
            return func.attr in PURE_METHODS
        return False

    def is_invariant_in(self, expression: ast.AST, loop: ast.AST) -> bool:
        """Whether `expression` evaluates to the same value on every iteration.

        True when it reads no name the loop rewrites and has no side effects.
        Constant literals are excluded by the caller, since hoisting them buys
        nothing.
        """
        if not self.is_pure(expression):
            return False
        return not (self.read_names(expression) & self.assigned_names(loop))


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
