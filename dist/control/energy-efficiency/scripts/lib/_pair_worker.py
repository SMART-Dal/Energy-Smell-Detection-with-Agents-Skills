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
import os
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

from lib._runner import burn_cpu, run_window  # noqa: E402
from lib.equivalence import normalise_text, render, render_json  # noqa: E402
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
    parent = importlib.import_module(parent_name) if parent_name else None
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
                raise
            skipped.append(_statement(node, lines, exc))
        except (Exception, SystemExit) as exc:  # noqa: BLE001
            skipped.append(_statement(node, lines, exc))
    return module


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


class LoadFailure(Exception):
    def __init__(self, stage: str):
        super().__init__(traceback.format_exc(limit=6))
        self.stage = stage


class Side:
    """One copy: its unit, its inputs, and the modules it was loaded from."""

    def __init__(self, root: str, workdir: str, unit: str, cases_source: str):
        self.root = os.path.realpath(root)
        self.workdir = Path(workdir).resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)
        # Longest first, so a scratch directory inside the copy is not half-replaced.
        self.replace = tuple(sorted(((self.root, "<REPO>"), (str(self.workdir), "<WORKDIR>")),
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
                target = module
                for piece in qualname.split("."):
                    target = getattr(target, piece)
                self.function = _callable_unit(target)
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

    def _enter_path(self) -> None:
        for entry in reversed(self.paths):
            sys.path.insert(0, entry)

    def _leave_path(self) -> None:
        for entry in self.paths:
            sys.path.remove(entry)

    def set_aside(self) -> None:
        """Take this copy's modules out of `sys.modules`, keeping them for later."""
        for name in [n for n, m in sys.modules.items() if _owned_by(m, self.root)]:
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


def main() -> int:
    protocol = os.fdopen(os.dup(1), "w", buffering=1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    sys.stdout = open(os.devnull, "w")

    def reply(payload: dict) -> None:
        protocol.write(json.dumps(payload) + "\n")
        protocol.flush()

    setup = json.loads(sys.stdin.readline())
    try:
        meter = get_meter(setup.get("meter", "auto"))
    except Exception:  # noqa: BLE001
        reply({"ok": False, "side": "before", "stage": "meter",
               "error": traceback.format_exc(limit=3)})
        return 1

    sides: dict[str, Side] = {}
    for name in ("before", "after"):
        try:
            sides[name] = Side(setup[f"{name}_root"], setup[f"{name}_workdir"],
                               setup["unit"], setup["cases_source"])
        except LoadFailure as failure:
            reply({"ok": False, "side": name, "stage": failure.stage, "error": str(failure)})
            return 1

    def described(side: Side) -> dict:
        equivalent = side.namespace.get("equivalent")
        return {
            "stubbed": list(side.stubbed),
            "skipped": list(side.skipped),
            "cases": [label for label, _ in side.sets["cases"]],
            "checks": [label for label, _ in side.sets["checks"]],
            "has_equivalent": callable(equivalent),
            "equivalent_doc": (getattr(equivalent, "__doc__", "") or "").strip(),
        }

    reply({"ok": True, "before": described(sides["before"]),
           "after": described(sides["after"])})

    active: Side | None = None
    for line in sys.stdin:
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
                reply(_check(side, request["set"], request["index"], request.get("plain", False)))
            elif op == "digest":
                reply({"ok": True, "digests": {key: side.digest(key) for key in request["keys"]}})
            elif op == "equivalent":
                function = side.namespace["equivalent"]
                reply({"ok": True, "same": bool(function(request["before"], request["after"]))})
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
            else:
                reply({"ok": False, "error": f"unknown op {op!r}"})
        except StubUsed as exc:
            reply({"ok": False, "stub_used": True, "error": str(exc)})
        except Exception:  # noqa: BLE001
            reply({"ok": False, "error": traceback.format_exc(limit=6)})
    return 0


def _check(side: Side, set_name: str, index: int, plain: bool) -> dict:
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
    files_before = side.files()
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        try:
            value, kind, raised = side.function(*args, **kwargs), "return", ""
        except StubUsed:
            raise
        except Exception as exc:  # noqa: BLE001 -- raising is behaviour to compare
            value, kind, raised = None, "raise", type(exc).__name__
    args_after = render_json(watched, replace=side.replace)
    files_after = side.files()
    written = {key: side.digest(key) for key, stat in files_after.items()
               if files_before.get(key) != stat}
    written.update({key: "absent" for key in files_before.keys() - files_after.keys()})
    result = {
        "ok": True,
        "kind": kind,
        "raised": raised,
        "value": render_json(value, replace=side.replace) if kind == "return" else "",
        "args_before": args_before,
        "args": args_after,
        "stdout": normalise_text(stream.getvalue(), side.replace),
        "mutates": args_before != args_after,
        "files": written,
    }
    if plain and kind == "return":
        result["plain"] = render(value, plain=True, replace=side.replace)
    return result


def _window(side: Side, request: dict, meter) -> dict:
    """One measured window: `repeats` calls, and nothing else.

    The argument pool is rebuilt before every window, outside the measured
    region, for a unit that mutates its input -- or the second window measures
    the inputs the first one already sorted, emptied or filled.
    """
    thunk = side.sets["cases"][request["index"]][1]
    repeats = request["repeats"]
    size = repeats if request.get("mutates") else 1
    pool = [_args(thunk) for _ in range(size)]

    index = request["index"]
    if index not in side.warmed:
        # Warm the code once per case, so neither side pays one-off costs --
        # lazy imports, the first allocation of a size class -- inside a window.
        loop, ready = _loop(pool)
        loop(side.function, ready, min(repeats, request.get("warmup_calls", 1)))
        side.warmed.add(index)
        if request.get("mutates"):
            pool = [_args(thunk) for _ in range(size)]

    loop, ready = _loop(pool)
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
