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
"""Different units one session may ask inputs for, failed ones included. More
than the 20 repairs it measures: room for units that cannot be generated and
for units decided against after asking. Until Oct 24, only 20 could hold inputs
at once and a ready unit never gave its place back, so two units rejected in
step 2 kept the two strongest candidates from getting any."""

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
        return None, (
            f"no inputs could be generated for {unit}: {entry.get('reason') or 'unknown'}. "
            f"If that is a package missing from this environment, install it into this "
            f"venv and request the unit again (`inputs.py request {unit}`); otherwise its "
            f"repairs cannot be measured here: record their suspicions as `blocked`, "
            f"with this reason.")
    if entry.get("state") != READY:
        return None, f"the inputs for {unit} are still being generated; run verify.py again"
    try:
        return (Path(directory) / file_name(unit)).read_text(), ""
    except OSError as exc:
        return None, f"the inputs for {unit} are listed as ready but cannot be read: {exc}"


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
