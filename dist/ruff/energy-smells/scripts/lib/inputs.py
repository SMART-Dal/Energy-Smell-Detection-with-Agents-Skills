"""Where the generated inputs live: one layout for inputs.py, verify.py and the generator.

The agent never writes the inputs a repair is measured on. It names the units
it will repair; a service outside the session generates each unit's inputs,
checks that they run on the original code, and writes them here, read-only:

    .energy-inputs/
        status.json                          every requested unit: pending, ready or failed
        <unit as a file name>.py             checks() and cases() for one unit

The service keeps its own copy of every file, and the review measures with that
copy, so a file edited here changes nothing but the agent's own reading.
"""

from __future__ import annotations

import json
import os
import re
import socket
import time
from pathlib import Path

DIRNAME = ".energy-inputs"
STATUS = "status.json"
SOCKET_ENV = "ENERGY_INPUTS_SOCKET"
MAX_UNITS = 30
"""Units one session may hold inputs for, ready or still being generated. A unit
whose generation failed gives its place back. More than the 20 repairs it
measures: room for units decided against after asking. Until Oct 24, only 20
could hold inputs at once and a ready unit never gave its place back, so two
units rejected in step 2 kept the two strongest candidates from getting any.
Until Oct 25 a failed unit kept its place too, so a session whose first picks
needed the network could be left with few units and no way to ask for more."""

MAX_FAILED = 30
"""Different units that may fail in one session; after that no new unit is
taken. Generation is paid for whether it succeeds or not, so failures have a
bound of their own now that they no longer count against `MAX_UNITS`. As many
as `MAX_UNITS`, not fewer: a session that asks for 30 at once and sees 25 fail
can still ask for 25 more."""

MAX_ATTEMPTS = 3
"""Times one unit may be generated in a session: a failed unit can be asked for
again, after the agent fixes what stopped it, but not without end."""

PENDING, READY, FAILED = "pending", "ready", "failed"


def file_name(unit: str) -> str:
    """`src/app.py::Report.render` -> `src_app.py__Report.render.py`."""
    path, _, qualname = unit.partition("::")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", path) + "__" + \
        re.sub(r"[^A-Za-z0-9_.-]+", "_", qualname) + ".py"


def read_status(directory: Path) -> dict:
    """`{unit: {"state": ..., "reason": ...}}`; empty when nothing was requested."""
    try:
        return json.loads((Path(directory) / STATUS).read_text()).get("units", {})
    except (OSError, ValueError):
        return {}


def read_limits(directory: Path) -> dict:
    """How many units hold inputs and how many failed, against their limits."""
    try:
        return json.loads((Path(directory) / STATUS).read_text()).get("limits", {})
    except (OSError, ValueError):
        return {}


def pending(directory: Path) -> list[str]:
    return sorted(u for u, s in read_status(directory).items() if s.get("state") == PENDING)


def inputs_for(unit: str, directory: Path) -> tuple[str | None, str]:
    """The unit's inputs as source text, or None and why there are none."""
    entry = read_status(directory).get(unit)
    if entry is None:
        return None, (
            f"no inputs were requested for {unit}. Request them -- `python "
            f"$SKILL/scripts/inputs.py request {unit}` -- and run verify.py again "
            f"once `inputs.py status` says they are ready.")
    if entry.get("state") == FAILED:
        return None, (f"no inputs could be generated for {unit}: "
                      f"{entry.get('reason') or 'unknown'}. Next: {what_next(unit, entry)}")
    if entry.get("state") != READY:
        return None, f"the inputs for {unit} are still being generated; run verify.py again"
    try:
        return (Path(directory) / file_name(unit)).read_text(), ""
    except OSError as exc:
        return None, f"the inputs for {unit} are listed as ready but cannot be read: {exc}"


_STUB_USED = re.compile(r"`?([A-Za-z_][\w.]*?)\.[\w]+`? was (?:read|called) while the unit ran")


def what_next(unit: str, entry: dict) -> str:
    """What to do about a unit whose inputs could not be generated, in one sentence.

    The same sentence in `inputs.py status` and in verify.py's `no_inputs`, so the
    agent is told once, where it looks, which of three cases it is in: something
    this venv can be given, something this machine cannot provide, or inputs the
    generator may manage on another try.
    """
    reason = entry.get("reason") or ""
    left = MAX_ATTEMPTS - entry.get("attempts", 1)
    again = f"ask for it again (`inputs.py request {unit}`)"
    blocked = ("its repairs cannot be measured here: record their suspicions as `blocked`, "
               "quoting this reason, and ask for the next unit you would measure instead "
               "-- a failed unit does not use up one of the 30")
    missing = re.search(r"No module named '([\w.]+)'", reason) or _STUB_USED.search(reason)
    if missing:
        package = missing.group(1).split(".")[0]
        if left <= 0:
            return f"`{package}` is missing from this venv, and the unit has had its {MAX_ATTEMPTS} tries; {blocked}"
        return (f"the unit needs `{package}`, which this venv does not have: install the "
                f"package that provides it into this venv (`pip install ...`) and {again}. "
                f"If it cannot be installed, {blocked}")
    if reason.startswith("it cannot run here") or reason.startswith("the unit's module does not load"):
        if left > 0 and re.search(r"install|not available|librar|package|module", reason, re.I):
            return (f"if what it lacks is a package, install it into this venv and {again}; "
                    f"otherwise {blocked}")
        return blocked
    if "changes from one run to the next" in reason:
        return f"the original itself gives a different output each time, so no input can fix it; {blocked}"
    if left <= 0:
        return f"the unit has had its {MAX_ATTEMPTS} tries; {blocked}"
    return (f"the generator writes new inputs on every try, so you may {again} "
            f"({left} {'try' if left == 1 else 'tries'} left); if it fails again, {blocked}")


def ask(request: dict, timeout: float = 60.0) -> dict:
    """One request to the input service; its answer, or {"ok": False, "error": ...}."""
    path = os.environ.get(SOCKET_ENV)
    if not path:
        return {"ok": False, "error": (
            "no input service is running in this environment, so no inputs can be "
            "generated here; repairs cannot be measured")}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(timeout)
            conn.connect(path)
            conn.sendall((json.dumps(request) + "\n").encode())
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
        return json.loads(data or b'{"ok": false, "error": "the input service closed the connection"}')
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": f"the input service did not answer: {exc}"}


def wait_until_settled(directory: Path, limit_s: float, log=print, poll_s: float = 5.0) -> list[str]:
    """Block while any requested unit is still being generated; what is left pending.

    Measuring while the service checks other units' inputs would share the
    machine with that work, so nothing is measured until every request is done.
    """
    started = time.monotonic()
    shown = None
    while True:
        left = pending(directory)
        if not left or time.monotonic() - started > limit_s:
            return left
        if left != shown:
            log(f"waiting for inputs still being generated: {len(left)} unit(s) "
                f"({', '.join(left[:3])}{', ...' if len(left) > 3 else ''})")
            shown = left
        time.sleep(poll_s)
