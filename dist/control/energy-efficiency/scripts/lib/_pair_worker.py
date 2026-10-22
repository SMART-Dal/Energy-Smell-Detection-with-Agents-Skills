"""Both copies of the repository, held open in one process.

Started once per submission. It imports the pristine copy, sets that copy's
modules aside, then imports the patched copy under the same names -- nothing is
renamed and no import is rewritten. Before anything runs on one side, that
side's modules are put back into `sys.modules` and its root back on `sys.path`
and into the working directory, so every import the unit makes, at load time
or lazily while running, binds to its own copy.

Why one process and not two, which was tried first. Two processes running
identical code do not run at identical speed: each carries its own offset of a
few percent -- layout, the core it landed on -- for as long as it lives. Reusing
one pair of processes repeated that offset, and identical code came back
"confirmed" in two of four runs; starting a fresh pair for every repetition
turned the offset into noise and widened the floor to 5-17%. Both copies in one
process, alternating on one thread, read like the same function measured
against itself: offsets under 1% across runs.

Speaks one JSON object per line: requests on stdin, replies on the original
stdout. The unit's own printing goes to /dev/null during measurement and is
captured during the equivalence check, so it can never corrupt the protocol.

Our helper package is called `lib`, and so are plenty of repositories' own.
Everything this worker needs from ours is imported first, then ours is removed
from `sys.modules` and `sys.path`, so a repository's own `lib` imports as itself.
"""

from __future__ import annotations

import __future__
import ast
import asyncio
import contextlib
import gc
import hashlib
import importlib
import importlib.util
import inspect
import io
import json
import logging
import os
import re
import statistics
import sys
import time
import tokenize
import traceback
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
_SCRIPTS = str(Path(__file__).resolve().parent.parent)
# Run by path, so Python put this file's own directory first on `sys.path`. It
# holds `models.py`, `measure.py` and others whose names a repository could
# share; it must not shadow anything the unit imports.
sys.path[:] = [p for p in sys.path if p not in (_HERE, "")]
sys.path.insert(0, _SCRIPTS)

from lib._runner import PoolTooLarge, build_pool, burn_cpu, run_window  # noqa: E402
from lib.equivalence import normalise_text, render_json  # noqa: E402
from lib.meters import get_meter  # noqa: E402
from lib.splice import split_name  # noqa: E402
from lib.stubs import StubUsed, import_with_stubs, importing, is_repo_module  # noqa: E402

for _name in [n for n in sys.modules if n == "lib" or n.startswith("lib.")]:
    del sys.modules[_name]
sys.path.remove(_SCRIPTS)


def _import_name(root: str, path: str) -> tuple[str, str, str]:
    """Where Python imports this file from, the name it has there, and its old name.

    The way the code itself runs. A module inside a package is imported from
    the directory above the package's top `__init__.py`, under its dotted
    package name: `tools/neptune_utils/streams.py` is `neptune_utils.streams`,
    from `tools/`. A standalone script is imported from its own directory under
    its file name, as `python tools/convert.py` finds it, so the sibling modules
    it imports resolve too.

    Naming every file from the repository root instead -- the old name, still
    registered as an alias so inputs written that way keep working -- made a
    package in a subdirectory import itself under a name its own absolute
    imports do not use. Those imports then failed, or were stubbed as if the
    repository's own package were a missing dependency.

    The exception is a file with relative imports in a directory without
    `__init__.py`, an implicit namespace package: its relative imports resolve
    only under the old name, so it keeps that one.
    """
    parts = list(Path(path).with_suffix("").parts)
    old = ".".join(parts)
    dirs, leaf = parts[:-1], ([] if parts[-1] == "__init__" else parts[-1:])
    depth = 0                   # how many enclosing directories are packages
    while depth < len(dirs) and Path(root, *dirs[:len(dirs) - depth], "__init__.py").is_file():
        depth += 1
    name = ".".join(dirs[len(dirs) - depth:] + leaf)
    if not name or (dirs and not depth and _has_relative_import(Path(root, path))):
        return root, old, old
    return str(Path(root, *dirs[:len(dirs) - depth])), name, old


def _has_relative_import(file: Path) -> bool:
    try:
        tree = ast.parse(file.read_bytes())
    except (OSError, SyntaxError, ValueError):
        return False
    return any(isinstance(node, ast.ImportFrom) and node.level for node in ast.walk(tree))


def _load_module(roots: list[Path], name: str, file: Path) -> tuple[object, list, list]:
    """Import the unit's module; if that fails, run as much of it as runs.

    A module is imported by running it top to bottom, so one failing statement
    anywhere in the file hides every function in it. Scripts do this often: a
    stray name after `sys.exit(main())`, which running the script never
    reaches, or arguments parsed at module level. So when the import fails, the
    module is run again one top-level statement at a time, and the statements
    that fail are skipped and reported -- the functions, classes and constants
    around them still load, unchanged. Both copies load the same way.
    """
    try:
        module, stubbed = import_with_stubs(roots, name)
        return module, stubbed, []
    except KeyboardInterrupt:
        raise
    except BaseException:  # noqa: BLE001 -- SystemExit too: a script's top-level code
        sys.modules.pop(name, None)
    skipped: list[str] = []
    module, stubbed = import_with_stubs(
        roots, name, load=lambda _: _run_statements(name, file, roots, skipped))
    return module, stubbed, skipped


def _run_statements(name: str, file: Path, roots: list[Path], skipped: list[str]):
    """Run a module one top-level statement at a time, skipping those that fail.

    A missing third-party package is still raised, so `import_with_stubs` can
    stand in for it and start again; everything else a statement raises skips
    that statement. `from __future__` flags carry over to the statements after
    them, as they would in one compiled module.
    """
    skipped.clear()
    with tokenize.open(file) as handle:
        source = handle.read()
    tree = ast.parse(source, str(file))
    lines = source.splitlines()
    parent_name, _, leaf = name.rpartition(".")
    parent = _parent_package(parent_name, file, roots, skipped) if parent_name else None
    if name in sys.modules:
        return sys.modules[name]        # loading the package loaded this module too
    spec = importlib.util.spec_from_file_location(
        name, file,
        submodule_search_locations=[str(file.parent)] if file.stem == "__init__" else None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    if parent is not None:
        setattr(parent, leaf, module)
    flags = 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            for alias in node.names:
                flags |= getattr(__future__, alias.name).compiler_flag
        code = compile(ast.Module(body=[node], type_ignores=[]), str(file), "exec",
                       flags=flags, dont_inherit=True)
        try:
            exec(code, module.__dict__)
        except ModuleNotFoundError as exc:
            if exc.name and not is_repo_module(roots, exc.name):
                # The retry, with a stub, runs this module again from the top;
                # left here, the half-run module came back as if loaded.
                sys.modules.pop(name, None)
                raise
            skipped.append(_statement(node, lines, exc))
        except (Exception, SystemExit) as exc:  # noqa: BLE001
            skipped.append(_statement(node, lines, exc))
    return module


def _parent_package(parent_name: str, file: Path, roots: list[Path], skipped: list[str]):
    """The package above a module, loaded statement by statement if it fails too.

    A package's `__init__` can fail for a reason that has nothing to do with
    the unit: porcupine's runs `KEYWORD_PATHS = pv_keyword_paths()`, which lists
    a resources folder that exists only once the package is installed, so no
    module under it could load, `PorcupineError.__str__` included. Its failing
    statements are skipped and reported like the module's own.
    """
    try:
        return importlib.import_module(parent_name)
    except ModuleNotFoundError as exc:
        if exc.name and not is_repo_module(roots, exc.name):
            raise                       # a missing library: import_with_stubs stands in for it
        failure = exc
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        failure = exc
    package_dir = file.parent if file.stem != "__init__" else file.parent.parent
    init = package_dir / "__init__.py"
    if not init.is_file():
        raise failure
    own: list[str] = []
    package = _run_statements(parent_name, init, roots, own)
    skipped.extend(f"{entry} in {parent_name.replace('.', '/')}/__init__.py" for entry in own)
    return package


def _statement(node, lines: list[str], exc: BaseException) -> str:
    text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "?"
    if len(text) > 60:
        text = text[:57] + "..."
    return f"line {node.lineno} `{text}` ({type(exc).__name__})"


def _owned_by(module, root: str) -> bool:
    """Was this module loaded from the copy under `root`?"""
    location = getattr(module, "__file__", None)
    if location:
        return os.path.realpath(location).startswith(root + os.sep)
    return any(os.path.realpath(p).startswith(root + os.sep)
               for p in getattr(module, "__path__", []) or [])


def _callable_unit(function):
    """What a call of the unit means, for the kinds of function that defer work.

    Calling an `async def` returns a coroutine and runs nothing; calling a
    generator function returns a generator and computes nothing. Measured as
    they are, both would time the creation of an object and compare two
    objects that never ran. So a coroutine is run to completion on this side's
    own event loop, and a generator is drained -- its output wrapped as
    `{"yielded": [...]}`, so a repair that turns a list into a generator still
    shows up as returning something different.
    """
    if inspect.iscoroutinefunction(function):
        loop = asyncio.new_event_loop()
        return lambda *args, **kwargs: loop.run_until_complete(function(*args, **kwargs))
    if inspect.isasyncgenfunction(function):
        loop = asyncio.new_event_loop()

        async def drain(*args, **kwargs):
            return [item async for item in function(*args, **kwargs)]
        return lambda *args, **kwargs: {"yielded": loop.run_until_complete(drain(*args, **kwargs))}
    if inspect.isgeneratorfunction(function):
        return lambda *args, **kwargs: {"yielded": list(function(*args, **kwargs))}
    return function


def _pairs(produced, what: str) -> list[tuple[str, object]]:
    """Validate `cases()`/`checks()` output: (label, thunk) pairs."""
    out = []
    for entry in produced:
        if not (isinstance(entry, tuple) and len(entry) == 2 and callable(entry[1])):
            raise ValueError(f"`{what}()` must return (label, thunk) pairs")
        out.append((str(entry[0]), entry[1]))
    labels = [label for label, _ in out]
    if len(set(labels)) != len(labels):
        raise ValueError(f"`{what}()` repeats a label: {labels}")
    return out


class Call:
    """`call(rows, sep=",")` in a thunk: arguments for a unit that takes keywords.

    A thunk normally returns a tuple, passed positionally. A keyword-only
    parameter cannot be reached that way, so `cases_source` is given `call`,
    which carries keyword arguments too.
    """

    __slots__ = ("args", "kwargs")

    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs


def _args(thunk) -> tuple[tuple, dict]:
    """A thunk's arguments, as positional and keyword."""
    produced = thunk()
    if isinstance(produced, Call):
        return produced.args, produced.kwargs
    if not isinstance(produced, tuple):
        raise ValueError(
            f"a thunk returned {type(produced).__name__}, expected a tuple of "
            f"arguments. A single argument needs a trailing comma: `lambda: (xs,)`; "
            f"keyword arguments go through `call`: `lambda: call(xs, key=1)`"
        )
    return produced, {}


def _loop(pool: list[tuple[tuple, dict]]):
    """The measured loop and the pool it runs over, chosen before measuring.

    A pool without keyword arguments runs exactly as it always has: the shared
    loop in `_runner`, over plain argument tuples. Only a pool with keywords
    takes the loop that passes them.
    """
    if any(kwargs for _, kwargs in pool):
        return _run_with_keywords, pool
    return run_window, [args for args, _ in pool]


def _run_with_keywords(function, pool: list[tuple[tuple, dict]], repeats: int) -> None:
    size = len(pool)
    for index in range(repeats):
        args, kwargs = pool[index % size]
        function(*args, **kwargs)


def _summary(exc: BaseException) -> str:
    """`RuntimeError: first line of its message`, for a reply a person reads.

    The last line of a traceback is the last line of the message, and a message
    can run to many lines: one that embedded /proc/cpuinfo reported itself as
    "power management:", which said nothing about what failed.
    """
    lines = str(exc).strip().splitlines()
    first = lines[0].strip() if lines else ""
    if len(first) > 200:
        first = first[:197] + "..."
    return f"{type(exc).__name__}: {first}" if first else type(exc).__name__


class LoadFailure(Exception):
    def __init__(self, stage: str):
        super().__init__(traceback.format_exc(limit=6))
        self.stage = stage
        self.summary = _summary(sys.exc_info()[1]) if sys.exc_info()[1] else ""


_ABSENT = object()

WATCH_LIMIT = 100_000
"""A watched container larger than this is compared by its type and size only:
rendering it twice for every checked call would cost more than the check."""

_DIGITS = re.compile(r"\d+")


def _is_data(value) -> bool:
    """Something a call can change, as opposed to code: not a module, class or function."""
    return not (inspect.ismodule(value) or inspect.isclass(value) or inspect.isroutine(value)
                or isinstance(value, (staticmethod, classmethod, property)))


def _code_names(function, module, owner) -> set[str]:
    """Every name the function's code uses -- globals and attributes alike -- and
    those of the functions it calls in its own module and class, a few levels down:
    where a write to state outside the arguments would be."""
    names: set[str] = set()
    queue, seen = [function], set()
    while queue and len(seen) < 64:
        try:
            code = getattr(inspect.unwrap(queue.pop()), "__code__", None)
        except ValueError:          # a wrapper cycle
            continue
        if code is None or code in seen:
            continue
        seen.add(code)
        own, stack = set(), [code]
        while stack:                # nested code: comprehensions, lambdas, inner defs
            current = stack.pop()
            own.update(current.co_names)
            stack.extend(const for const in current.co_consts if inspect.iscode(const))
        names |= own
        for name in own:
            for space in (vars(module), vars(owner) if owner is not None else {}):
                callee = space.get(name)
                if isinstance(callee, (staticmethod, classmethod)):
                    callee = callee.__func__
                if inspect.isfunction(callee) and callee.__module__ == module.__name__:
                    queue.append(callee)
    return names


def _watch(function, module, owner) -> list[tuple[str, str]]:
    """The module globals and class attributes to compare after every checked call.

    Only those the original's code names: a write to anything else would have to
    go through a name the code does not contain. Read from the original, so a
    new global the repair keeps for itself -- a cache -- is its own business.
    """
    names = _code_names(function, module, owner)
    keys = [("global", name) for name in sorted(names)
            if not name.startswith("__") and name in vars(module) and _is_data(vars(module)[name])]
    classes = {owner.__qualname__: owner} if owner is not None else {}
    for name in names:
        value = vars(module).get(name)
        if inspect.isclass(value) and value.__module__ == module.__name__:
            classes[value.__qualname__] = value
    for qualname, cls in sorted(classes.items()):
        keys += [("class", f"{qualname}.{name}") for name in sorted(names)
                 if not name.startswith("__") and name in vars(cls) and _is_data(vars(cls)[name])]
    return keys


def _watched_render(value, replace: tuple) -> str:
    if value is _ABSENT:
        return "absent"
    try:
        size = len(value)
    except Exception:  # noqa: BLE001 -- no length: render it
        size = None
    if size is not None and size > WATCH_LIMIT and not isinstance(value, (str, bytes)):
        return f"{type(value).__qualname__} of {size}"
    return render_json(value, replace=replace)


class _LogRecords(logging.Handler):
    """Every log record a call emits: logger, level and message, digits blanked
    so that a duration or a timestamp in the text does not count as a difference."""

    def __init__(self, replace: tuple):
        super().__init__(logging.NOTSET)
        self.replace, self.lines = replace, []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 -- a malformed call to the logger
            message = str(record.msg)
        message = _DIGITS.sub("N", normalise_text(message, self.replace))
        self.lines.append(f"{record.name} {record.levelname}: {message}")


class Side:
    """One copy: its unit, its inputs, and the modules it was loaded from."""

    def __init__(self, root: str, workdir: str, unit: str, cases_source: str):
        self.root = os.path.realpath(root)
        self.workdir = Path(workdir).resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)
        # Longest first, so a scratch directory inside the copy is not half-replaced.
        # The scratch directory relative to the copy (calls run with the copy as
        # cwd) differs between the sides too: an input built with os.path.relpath
        # printed `../io-before/...` beside `../io-after/...`, and a correct
        # repair came back not_equivalent (Oct 21).
        relative = os.path.relpath(self.workdir, self.root)
        self.replace = tuple(sorted(((self.root, "<REPO>"), (str(self.workdir), "<WORKDIR>"),
                                     (relative, "<WORKDIR>")),
                                    key=lambda pair: -len(pair[0])))
        self.modules: dict = {}
        self.warmed: set[int] = set()
        self.stubbed: list = []
        self.skipped: list = []

        try:
            path, qualname = split_name(unit)
            import_root, name, old_name = _import_name(self.root, path)
        except Exception:  # noqa: BLE001
            raise LoadFailure("import")
        self.unit_files = {os.path.join(self.root, path), os.path.realpath(os.path.join(self.root, path))}
        # The import root first, as Python would put it; the repository root
        # stays on the path for inputs that import from the top.
        self.paths = list(dict.fromkeys([import_root, self.root]))
        self._enter_path()
        os.chdir(self.root)
        try:
            try:
                module, self.stubbed, self.skipped = _load_module(
                    [Path(entry) for entry in self.paths], name, Path(self.root, path))
                if old_name != name:
                    sys.modules.setdefault(old_name, module)
                owner = target = module
                for piece in qualname.split("."):
                    if not hasattr(target, piece) and self.skipped:
                        # Usually a class whose statement failed, because an
                        # import above it did: name that, not just the absence.
                        stand_ins = (f", with stand-ins for {', '.join(self.stubbed)}"
                                     if self.stubbed else "")
                        raise AttributeError(f"{piece} is not defined here: loading the module "
                                             f"skipped {'; '.join(self.skipped[:2])}{stand_ins}")
                    owner, target = target, getattr(target, piece)
                if isinstance(inspect.getattr_static(owner, piece, None), classmethod):
                    # Looked up on its class, a classmethod comes back bound to
                    # it. Called as a plain function like every other method, it
                    # takes its class first -- what the inputs pass.
                    target = target.__func__
                self.function = _callable_unit(target)
                self.module, self.target = module, target
                self.owner = owner if inspect.isclass(owner) else None
                self.watched: list[tuple[str, str]] = []
            except (Exception, SystemExit):  # noqa: BLE001
                raise LoadFailure("import")
            try:
                self.namespace: dict = {"__name__": "_cases", "WORKDIR": self.workdir,
                                        "call": Call}
                # Module-level code in the factory -- importing the repository's
                # other modules -- is loading, like the unit's own import.
                # Stand-ins pass through here; what the thunks or the unit do
                # later is still refused.
                with importing():
                    exec(compile(cases_source, "<cases_source>", "exec"), self.namespace)
                for name in ("cases", "checks"):
                    if not callable(self.namespace.get(name)):
                        raise ValueError(f"`cases_source` defines no `{name}()`")
                self.sets = {name: _pairs(self.namespace[name](), name)
                             for name in ("cases", "checks")}
            except Exception:  # noqa: BLE001
                raise LoadFailure("cases")
        finally:
            self.set_aside()
            self._leave_path()

    def state(self) -> dict[str, str]:
        """The watched module- and class-level values on this side, rendered."""
        out = {}
        for kind, name in self.watched:
            if kind == "global":
                value = vars(self.module).get(name, _ABSENT)
            else:
                qualname, _, attribute = name.rpartition(".")
                owner = self.module
                for piece in qualname.split("."):
                    owner = getattr(owner, piece, None)
                value = vars(owner).get(attribute, _ABSENT) if inspect.isclass(owner) else _ABSENT
            out[f"{kind}:{name}"] = _watched_render(value, self.replace)
        return out

    def _enter_path(self) -> None:
        for entry in reversed(self.paths):
            sys.path.insert(0, entry)

    def _leave_path(self) -> None:
        for entry in self.paths:
            sys.path.remove(entry)

    def set_aside(self) -> None:
        """Take this copy's modules out of `sys.modules`, keeping them for later."""
        # Over a copy: `_owned_by` reads `__file__`, and a lazily loaded module
        # (transformers, for one) imports more modules on that read.
        for name in [n for n, m in list(sys.modules.items()) if _owned_by(m, self.root)]:
            self.modules[name] = sys.modules.pop(name)

    def activate(self) -> None:
        """Make this copy the one every import, path and file resolves to."""
        sys.modules.update(self.modules)
        self._enter_path()
        os.chdir(self.root)

    def deactivate(self) -> None:
        self.set_aside()       # including anything imported lazily since
        self._leave_path()

    def files(self) -> dict[str, tuple[int, int]]:
        """Every file in this copy and its scratch directory: name -> (mtime, size)."""
        found = {}
        for base, label in ((Path(self.root), "<REPO>"), (self.workdir, "<WORKDIR>")):
            for directory, subdirs, names in os.walk(base):
                subdirs[:] = [d for d in subdirs if d != "__pycache__"]
                for entry in names:
                    full = os.path.join(directory, entry)
                    try:
                        stat = os.stat(full)
                    except OSError:
                        continue
                    found[f"{label}/{os.path.relpath(full, base)}"] = (stat.st_mtime_ns,
                                                                      stat.st_size)
        return found

    def digest(self, key: str) -> str:
        """A file's content, with this copy's own paths normalised away; `absent` if none."""
        label, _, relative = key.partition("/")
        base = Path(self.root) if label == "<REPO>" else self.workdir
        try:
            data = (base / relative).read_bytes()
        except OSError:
            return "absent"
        try:
            data = normalise_text(data.decode("utf-8"), self.replace).encode("utf-8")
        except UnicodeDecodeError:
            pass
        return hashlib.sha256(data).hexdigest()[:16]


def _metric_collectors() -> set:
    """The collectors in prometheus_client's process-wide registry, if it is loaded."""
    registry = getattr(sys.modules.get("prometheus_client.registry"), "REGISTRY", None)
    return set(getattr(registry, "_collector_to_names", {})) if registry else set()


def _forget_metrics(known: set) -> None:
    """Unregister the metrics one copy registered while it loaded.

    prometheus_client keeps one registry per process and refuses a second metric
    of the same name, so the patched copy's import of a module that defines its
    metrics at top level failed with "Duplicated timeseries" -- every feast
    module that reaches `feast.metrics`. The metric objects keep working
    unregistered; the registry only collects them for export.
    """
    registry = getattr(sys.modules.get("prometheus_client.registry"), "REGISTRY", None)
    for collector in _metric_collectors() - known:
        try:
            registry.unregister(collector)
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    protocol = os.fdopen(os.dup(1), "w", buffering=1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    sys.stdout = open(os.devnull, "w")
    # Requests come in on a copy of stdin; the code under test gets an empty one.
    # A script that asks for a key at import time (`os.getenv(...) or input(...)`)
    # read our protocol pipe, blocked until the 60 s load deadline, and was
    # reported as "builds too much" (Oct 22). Now its input() ends at once.
    requests = os.fdopen(os.dup(0), "r")
    nothing = os.open(os.devnull, os.O_RDONLY)
    os.dup2(nothing, 0)
    sys.stdin = open(os.devnull, "r")

    def reply(payload: dict) -> None:
        protocol.write(json.dumps(payload) + "\n")
        protocol.flush()

    setup = json.loads(requests.readline())
    try:
        meter = get_meter(setup.get("meter", "auto"))
    except Exception:  # noqa: BLE001
        reply({"ok": False, "side": "before", "stage": "meter",
               "error": traceback.format_exc(limit=3)})
        return 1

    sides: dict[str, Side] = {}
    for name in ("before", "after"):
        known = _metric_collectors()
        try:
            sides[name] = Side(setup[f"{name}_root"], setup[f"{name}_workdir"],
                               setup["unit"], setup["cases_source"])
        except LoadFailure as failure:
            reply({"ok": False, "side": name, "stage": failure.stage, "error": str(failure),
                   "summary": failure.summary})
            return 1
        _forget_metrics(known)
    watched = _watch(sides["before"].target, sides["before"].module, sides["before"].owner)
    for side in sides.values():
        side.watched = watched

    def described(side: Side) -> dict:
        return {
            "stubbed": list(side.stubbed),
            "skipped": list(side.skipped),
            "cases": [label for label, _ in side.sets["cases"]],
            "checks": [label for label, _ in side.sets["checks"]],
            "watched": [f"{kind}:{name}" for kind, name in side.watched],
        }

    reply({"ok": True, "before": described(sides["before"]),
           "after": described(sides["after"])})

    active: Side | None = None
    for line in requests:
        request = json.loads(line)
        op = request["op"]
        try:
            if op == "warm":
                burn_cpu(request["seconds"])
                reply({"ok": True})
                continue
            side = sides[request["side"]]
            if active is not side:
                if active is not None:
                    active.deactivate()
                side.activate()
                active = side
            if op == "check":
                reply(_check(side, request["set"], request["index"]))
            elif op == "digest":
                reply({"ok": True, "digests": {key: side.digest(key) for key in request["keys"]}})
            elif op == "time":
                thunk = side.sets["cases"][request["index"]][1]
                timings = []
                for _ in range(request.get("calls", 5)):
                    args, kwargs = _args(thunk)
                    start = time.perf_counter()
                    side.function(*args, **kwargs)
                    timings.append(time.perf_counter() - start)
                # Median, not minimum: the fastest call met the warmest cache.
                reply({"ok": True, "seconds": statistics.median(timings)})
            elif op == "window":
                reply(_window(side, request, meter))
            elif op == "pool":
                # Whether a window of `repeats` calls could build its fresh
                # arguments, for an input that is still being chosen.
                thunk = side.sets["cases"][request["index"]][1]
                try:
                    build_pool(lambda: _args(thunk), request["repeats"])
                    reply({"ok": True, "fits": True})
                except PoolTooLarge as exc:
                    reply({"ok": True, "fits": False, "why": str(exc)})
            elif op == "lines":
                reply({"ok": True, "lines": _lines_run(side, request["set"], request["index"])})
            else:
                reply({"ok": False, "error": f"unknown op {op!r}"})
        except StubUsed as exc:
            reply({"ok": False, "stub_used": True, "error": str(exc)})
        except PoolTooLarge as exc:
            reply({"ok": False, "error": str(exc), "summary": str(exc)})
        except Exception as exc:  # noqa: BLE001
            reply({"ok": False, "error": traceback.format_exc(limit=6), "summary": _summary(exc)})
    return 0


def _check(side: Side, set_name: str, index: int) -> dict:
    """Run one input on one side and render every observable channel.

    Files count as output: every file the call creates, changes or deletes, in
    the scratch directory or in this copy of the repository, is reported with
    a digest of what it ends up holding. Taken after the inputs are built, so a
    thunk writing its input file is not mistaken for the unit's output.
    """
    args, kwargs = _args(side.sets[set_name][index][1])
    # The keyword arguments are watched for mutation too; a positional-only
    # call renders exactly as it always has.
    watched = (args, kwargs) if kwargs else args
    args_before = render_json(watched, replace=side.replace)
    state_before = side.state()
    files_before = side.files()
    stream = io.StringIO()
    message = ""
    records = _LogRecords(side.replace)
    logging.getLogger().addHandler(records)
    try:
        with contextlib.redirect_stdout(stream):
            try:
                value, kind, raised = side.function(*args, **kwargs), "return", ""
            except StubUsed:
                raise
            except (Exception, SystemExit) as exc:  # noqa: BLE001 -- raising is behaviour to compare
                # SystemExit too: csv-gremlin's process_property calls sys.exit on a
                # malformed row, which is what it does, and used to kill the worker.
                value, kind, raised = None, "raise", type(exc).__name__
                message = _summary(exc)
    finally:
        logging.getLogger().removeHandler(records)
    args_after = render_json(watched, replace=side.replace)
    state_after = side.state()
    files_after = side.files()
    written = {key: side.digest(key) for key, stat in files_after.items()
               if files_before.get(key) != stat}
    written.update({key: "absent" for key in files_before.keys() - files_after.keys()})
    result = {
        "ok": True,
        "kind": kind,
        "raised": raised,
        "message": message,
        "value": render_json(value, replace=side.replace) if kind == "return" else "",
        "args_before": args_before,
        "args": args_after,
        "stdout": normalise_text(stream.getvalue(), side.replace),
        "mutates": args_before != args_after,
        "files": written,
        # Module globals and class attributes the original's code names, and
        # what the call logged: behaviour outside the return value and the
        # arguments, which a repair could otherwise drop to look cheaper.
        "state": {key: rendered for key, rendered in state_after.items()
                  if state_before.get(key) != rendered},
        "log": records.lines,
    }
    return result


def _lines_run(side: Side, set_name: str, index: int) -> list[int]:
    """The lines of the unit's file that one call on one input executes.

    For the input generator, which checks that its inputs reach the unit's
    real work rather than an early return. Never used while measuring: the
    tracing slows every line it watches.
    """
    args, kwargs = _args(side.sets[set_name][index][1])
    seen: set[int] = set()

    def local(frame, event, arg):
        if event == "line":
            seen.add(frame.f_lineno)
        return local

    def tracer(frame, event, arg):
        return local if frame.f_code.co_filename in side.unit_files else None

    sys.settrace(tracer)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            side.function(*args, **kwargs)
    except (Exception, SystemExit):  # noqa: BLE001 -- what ran before it raised still counts
        pass
    finally:
        sys.settrace(None)
    return sorted(seen)


def _window(side: Side, request: dict, meter) -> dict:
    """One measured window: `repeats` calls, and nothing else.

    Every call gets fresh arguments, from a pool built before the window,
    outside the measured region (`build_pool`).
    """
    thunk = side.sets["cases"][request["index"]][1]
    repeats = request["repeats"]

    index = request["index"]
    if index not in side.warmed:
        # Warm the code once per case, so neither side pays one-off costs --
        # lazy imports, the first allocation of a size class -- inside a window.
        warm = min(repeats, request.get("warmup_calls", 1))
        loop, ready = _loop(build_pool(lambda: _args(thunk), warm))
        loop(side.function, ready, warm)
        side.warmed.add(index)

    loop, ready = _loop(build_pool(lambda: _args(thunk), repeats))
    gc.collect()
    sample = meter.sample(lambda: loop(side.function, ready, repeats))
    return {
        "ok": True,
        "energy_j": sample.energy_j,
        "duration_s": sample.duration_s,
        "power_w": sample.power_w,
        "domains": sorted(sample.domains_j or {}),
    }


if __name__ == "__main__":
    raise SystemExit(main())
