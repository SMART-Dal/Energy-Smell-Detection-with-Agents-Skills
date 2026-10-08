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

import asyncio
import contextlib
import gc
import inspect
import io
import json
import os
import statistics
import sys
import time
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
from lib.stubs import StubUsed, import_with_stubs, importing  # noqa: E402

for _name in [n for n in sys.modules if n == "lib" or n.startswith("lib.")]:
    del sys.modules[_name]
sys.path.remove(_SCRIPTS)


def _module_name(path: str) -> str:
    """`pkg/sub/mod.py` -> `pkg.sub.mod`; a flat script is just `mod`."""
    return ".".join(Path(path).with_suffix("").parts)


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
        return lambda *args: loop.run_until_complete(function(*args))
    if inspect.isasyncgenfunction(function):
        loop = asyncio.new_event_loop()

        async def drain(*args):
            return [item async for item in function(*args)]
        return lambda *args: {"yielded": loop.run_until_complete(drain(*args))}
    if inspect.isgeneratorfunction(function):
        return lambda *args: {"yielded": list(function(*args))}
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


def _args(thunk) -> tuple:
    produced = thunk()
    if not isinstance(produced, tuple):
        raise ValueError(
            f"a thunk returned {type(produced).__name__}, expected a tuple of "
            f"arguments. A single argument needs a trailing comma: `lambda: (xs,)`"
        )
    return produced


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

        sys.path.insert(0, self.root)
        os.chdir(self.root)
        try:
            try:
                path, qualname = split_name(unit)
                module, self.stubbed = import_with_stubs(Path(self.root), _module_name(path))
                target = module
                for piece in qualname.split("."):
                    target = getattr(target, piece)
                self.function = _callable_unit(target)
            except Exception:  # noqa: BLE001
                raise LoadFailure("import")
            try:
                self.namespace: dict = {"__name__": "_cases", "WORKDIR": self.workdir}
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
            sys.path.remove(self.root)

    def set_aside(self) -> None:
        """Take this copy's modules out of `sys.modules`, keeping them for later."""
        for name in [n for n, m in sys.modules.items() if _owned_by(m, self.root)]:
            self.modules[name] = sys.modules.pop(name)

    def activate(self) -> None:
        """Make this copy the one every import, path and file resolves to."""
        sys.modules.update(self.modules)
        sys.path.insert(0, self.root)
        os.chdir(self.root)

    def deactivate(self) -> None:
        self.set_aside()       # including anything imported lazily since
        sys.path.remove(self.root)


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
            elif op == "equivalent":
                function = side.namespace["equivalent"]
                reply({"ok": True, "same": bool(function(request["before"], request["after"]))})
            elif op == "time":
                thunk = side.sets["cases"][request["index"]][1]
                timings = []
                for _ in range(request.get("calls", 5)):
                    args = _args(thunk)
                    start = time.perf_counter()
                    side.function(*args)
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
    """Run one input on one side and render every observable channel."""
    args = _args(side.sets[set_name][index][1])
    args_before = render_json(args, replace=side.replace)
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        try:
            value, kind, raised = side.function(*args), "return", ""
        except StubUsed:
            raise
        except Exception as exc:  # noqa: BLE001 -- raising is behaviour to compare
            value, kind, raised = None, "raise", type(exc).__name__
    args_after = render_json(args, replace=side.replace)
    result = {
        "ok": True,
        "kind": kind,
        "raised": raised,
        "value": render_json(value, replace=side.replace) if kind == "return" else "",
        "args_before": args_before,
        "args": args_after,
        "stdout": normalise_text(stream.getvalue(), side.replace),
        "mutates": args_before != args_after,
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
        run_window(side.function, pool, min(repeats, request.get("warmup_calls", 1)))
        side.warmed.add(index)
        if request.get("mutates"):
            pool = [_args(thunk) for _ in range(size)]

    gc.collect()
    sample = meter.sample(lambda: run_window(side.function, pool, repeats))
    return {
        "ok": True,
        "energy_j": sample.energy_j,
        "duration_s": sample.duration_s,
        "power_w": sample.power_w,
        "domains": sorted(sample.domains_j or {}),
    }


if __name__ == "__main__":
    raise SystemExit(main())
