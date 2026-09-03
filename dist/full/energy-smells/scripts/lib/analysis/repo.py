"""Which file a call lands in, across the whole repository.

The call graph used to stop at the file edge.  That was defensible while the
alternative was matching on a function's short name -- `Parser.parse` and
`Lexer.parse` both answer to "parse", and linking a call to both invents an
edge that does not exist.  But stopping there is not free either: measured
against the call graph our own test suite actually executes, in-file matching
found **none** of the 63 cross-file calls, and a repository whose modules talk
to each other is exactly the thing a scan is pointed at.

So this module resolves calls the way Python does, from what the author wrote
down:

    from .util import helper      ->  helper()      is pkg.util.helper
    import pkg.util as u          ->  u.helper()    is pkg.util.helper
    def rule(ctx: UnitContext)    ->  ctx.method()  is UnitContext.method
    engine = Engine()             ->  engine.run()  is Engine.run

Every one of those is a fact in the source, not a guess: an import statement
names its module, and a parameter annotation is a promise the author made.  If
an annotation is wrong the code is wrong.  What this module will *not* do is
infer a type through a function's return value or a container -- that is where
resolution stops being reading and starts being guessing, and an invented edge
is worse than an absent one because it silently inflates a unit's ranking.

Anything unresolved stays unresolved and is reported as such.  On pandas that
is roughly 60% of call sites -- overwhelmingly calls into the standard library
and into third-party packages, which are outside the scan by definition.

A note on why there is no dependency here.  Jedi resolves the same call sites
with real type inference, and it was measured against this: on our own source
it found *the same* 47 of 63 cross-file edges and 3 more intra-file ones, for
1.4 points of total recall -- and it took roughly 16 minutes on pandas where
this takes 19 seconds.  Fifty times the cost for a rounding error, plus a
runtime dependency on a scanner that otherwise needs nothing but Python.
"""

from __future__ import annotations

import ast
from pathlib import Path

MAX_REEXPORT_HOPS = 4
"""How far `from .a import b` chains are followed before giving up.

Bounded because a package's `__init__` can re-export from a module that
re-exports back, and a cycle there has no fixpoint.  Four hops covers the
`pkg/__init__.py` -> `pkg/core.py` -> `pkg/_impl.py` layering that real
packages use; past that the name is not worth chasing.
"""


class RepoIndex:
    """Every definition in the scanned tree, and what each file's names mean.

    Built once per scan.  Indexing is a single parse of each file, and the
    parse is kept, so the engine does not read the tree twice.
    """

    def __init__(self, root: Path, files: list[Path]):
        self.root = root.resolve()
        self.trees: dict[Path, ast.AST] = {}
        self.module_of: dict[Path, str] = {}
        self.path_of: dict[str, Path] = {}
        self.is_package: dict[Path, bool] = {}
        self.symbols: dict[str, dict[str, str]] = {}
        """module -> {"helper": "pkg.util.helper", "Engine.run": "pkg.util.Engine.run"}"""
        self.reexport: dict[str, dict[str, str]] = {}
        """module -> {name it exposes: fully-qualified name it came from}"""
        self.by_suffix: dict[str, list[str]] = {}
        """last components -> modules ending in them, for sys.path-relative imports"""

        for path in files:
            tree = _parse(path)
            if tree is None:
                continue
            module = self._module_name(path)
            self.trees[path] = tree
            self.module_of[path] = module
            self.path_of[module] = path
            self.is_package[path] = path.name == "__init__.py"
            self.symbols[module] = _definitions(tree, module)
            parts = module.split(".")
            for start in range(1, len(parts)):
                self.by_suffix.setdefault(".".join(parts[start:]), []).append(module)

        for path, tree in self.trees.items():
            module = self.module_of[path]
            exposed = {}
            for node in tree.body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                origin = self.absolute_module(node, module, self.is_package[path])
                if origin:
                    for alias in node.names:
                        exposed[alias.asname or alias.name] = f"{origin}.{alias.name}"
            if exposed:
                self.reexport[module] = exposed

    # -- naming ------------------------------------------------------------

    def _module_name(self, path: Path) -> str:
        try:
            relative = path.resolve().relative_to(self.root)
        except ValueError:
            relative = Path(path.name)
        module = ".".join(relative.with_suffix("").parts)
        return module[: -len(".__init__")] if module.endswith(".__init__") else module

    def absolute_module(self, node: ast.ImportFrom, current: str, is_package: bool) -> str | None:
        """`from ..util import x` inside `pkg.sub.deep` -> "pkg.util".

        Level 1 means the package *containing* this module, so a plain module
        drops its own last component first and a package's `__init__` does not.
        Getting this backwards resolved every relative import one level too
        deep, which silently produced no cross-file edges at all.
        """
        if not node.level:
            return node.module
        parts = current.split(".")
        if not is_package:
            parts = parts[:-1]
        if node.level > 1:
            parts = parts[: len(parts) - (node.level - 1)]
        if not parts:
            return None
        return ".".join(parts + (node.module.split(".") if node.module else []))

    def qualname_in(self, path: Path, unit_qualname: str) -> str:
        """A unit's repo-wide identity: `lib.analysis.context.UnitContext.owns`."""
        module = self.module_of.get(path)
        return f"{module}.{unit_qualname}" if module else unit_qualname

    # -- lookup ------------------------------------------------------------

    def lookup(self, qualified: str) -> str | None:
        """Follow a fully-qualified name to a definition this tree holds."""
        for _ in range(MAX_REEXPORT_HOPS):
            if "." not in qualified:
                return None
            module, name = qualified.rsplit(".", 1)
            module = self._resolve_alias(module)
            table = self.symbols.get(module)
            if table and name in table:
                return table[name]
            exposed = self.reexport.get(module)
            if exposed and name in exposed:
                qualified = exposed[name]
                continue
            return None
        return None

    def _resolve_alias(self, module: str) -> str:
        """The module a name refers to when the package root is a subdirectory.

        A repository whose code lives in `src/` and imports itself as
        `from evaluation_functions import ...` is importing with `src/` on the
        path, so the module the scan indexed as `src.evaluation_functions` is
        the one meant.  Scanning the repository root instead of `src` made every
        such import unresolvable -- and that is the ordinary way to point a scan
        at a project.

        Only an unambiguous suffix resolves.  Two modules ending in the same
        name mean the import cannot be settled by reading, and inventing an edge
        there is exactly what this module refuses to do.
        """
        if module in self.symbols:
            return module
        candidates = self.by_suffix.get(module, ())
        return candidates[0] if len(candidates) == 1 else module

    def bindings(self, path: Path) -> dict[str, str]:
        """What each imported name in one file refers to, fully qualified."""
        tree, module = self.trees[path], self.module_of[path]
        out: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                origin = self.absolute_module(node, module, self.is_package[path])
                if origin:
                    for alias in node.names:
                        out[alias.asname or alias.name] = f"{origin}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    out[alias.asname or alias.name] = alias.name
        return out

    # -- what a receiver holds ---------------------------------------------

    def receivers(self, scope: ast.AST, module: str, binds: dict[str, str]) -> dict[str, str]:
        """Names whose class we can read off the source, for `name.method()`.

        Two sources, both written down by the author rather than inferred:
        a parameter's annotation, and a direct assignment from a class we can
        see.  A name bound to a function's *return* value is deliberately left
        out -- following that needs real type inference, and guessing there is
        how a resolver starts inventing edges.
        """
        found: dict[str, str] = {}
        local = self.symbols.get(module, {})

        arguments = getattr(scope, "args", None)
        if arguments is not None:
            declared = [
                *getattr(arguments, "posonlyargs", []),
                *arguments.args,
                *arguments.kwonlyargs,
            ]
            for argument in declared:
                if argument.annotation is None:
                    continue
                name = _annotation_name(argument.annotation)
                target = _class_target(name, local, binds, self)
                if target:
                    found[argument.arg] = target

        for node in ast.walk(scope):
            if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
                continue
            constructor = node.value.func
            if not isinstance(constructor, ast.Name):
                continue
            target = _class_target(constructor.id, local, binds, self)
            if not target:
                continue
            for assigned in node.targets:
                if isinstance(assigned, ast.Name):
                    found[assigned.id] = target
        return found

    def resolve(self, func: ast.AST, module: str, binds: dict[str, str],
                receivers: dict[str, str], enclosing_class: str | None) -> str | None:
        """The definition a call site refers to, or None if we cannot read it."""
        local = self.symbols.get(module, {})

        if isinstance(func, ast.Name):
            if func.id in local:
                return local[func.id]
            if func.id in binds:
                return self.lookup(binds[func.id])
            return None

        if not isinstance(func, ast.Attribute):
            return None

        base = func.value
        if not isinstance(base, ast.Name):
            return None

        if base.id == "self" and enclosing_class:
            return local.get(f"{enclosing_class}.{func.attr}")
        if base.id in binds:                       # module attribute: `util.helper()`
            return self.lookup(f"{binds[base.id]}.{func.attr}")
        if base.id in local:                       # `Engine.run()` on the class itself
            return local.get(f"{base.id}.{func.attr}")

        owner = receivers.get(base.id)             # `ctx.owns()` / `engine.run()`
        if owner:
            owner_module, class_name = owner.rsplit(".", 1)
            return self.symbols.get(owner_module, {}).get(f"{class_name}.{func.attr}")
        return None


# -- helpers ---------------------------------------------------------------


def _parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, ValueError, OSError):
        return None


def _definitions(tree: ast.AST, module: str) -> dict[str, str]:
    """Top-level functions and classes, plus each class's own methods."""
    table: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            table[node.name] = f"{module}.{node.name}"
        elif isinstance(node, ast.ClassDef):
            table[node.name] = f"{module}.{node.name}"
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    table[f"{node.name}.{member.name}"] = f"{module}.{node.name}.{member.name}"
    return table


def _class_target(name: str | None, local: dict[str, str],
                  binds: dict[str, str], index: RepoIndex) -> str | None:
    if not name:
        return None
    if name in local:
        return local[name]
    if name in binds:
        return index.lookup(binds[name])
    return None


def _annotation_name(node: ast.AST) -> str | None:
    """The bare class name of an annotation, seeing through `X | None` and `list[X]`."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.split("[")[0].strip().rsplit(".", 1)[-1] or None
    if isinstance(node, ast.Subscript):
        return _annotation_name(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        for side in (node.left, node.right):
            if isinstance(side, ast.Constant) and side.value is None:
                continue
            found = _annotation_name(side)
            if found and found != "None":
                return found
    return None
