"""Two copies of a repository, loaded side by side in one process.

`before` is a pristine copy. `after` is a copy with the submission's
replacements spliced into the files they name. One worker (`_pair_worker.py`)
imports both under their real package names -- the first copy's modules are
set aside while the second is imported, and swapped back before anything runs
on its side -- so nothing is renamed and no import is rewritten.

The two sides alternate on one thread, one measured window each, so every
paired sample sits a few seconds from its partner, on the same core and in the
same address space. `_pair_worker.py` records why this is one process rather
than two: two processes running identical code differ by a few percent for as
long as they live, and that offset read as a saving.

Each side gets its own scratch directory (`WORKDIR` in `cases_source`) and its
own copy of the input factory, so whatever one side writes the other never
sees.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .splice import splice_tree

WORKER = Path(__file__).resolve().parent / "_pair_worker.py"

IGNORED = shutil.ignore_patterns(
    ".git", ".hg", ".svn", "__pycache__", "*.pyc", ".venv", "venv", "env",
    "node_modules", ".tox", ".nox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "*.egg-info", ".eggs",
)
"""Never copied: version control, environments and caches. None of it is code
the unit can import, and some of it (a virtualenv, `node_modules`) is most of
the bytes in a checkout."""


class LoadError(RuntimeError):
    """A side could not load. `stage` says which part, `side` which copy."""

    def __init__(self, side: str, stage: str, message: str):
        super().__init__(message)
        self.side, self.stage = side, stage


class WorkerError(RuntimeError):
    """A side failed while running a request."""

    def __init__(self, message: str, *, stub_used: bool = False):
        super().__init__(message)
        self.stub_used = stub_used


def stage(repo: Path, changed: dict[str, str], work: Path) -> tuple[Path, Path]:
    """A pristine copy and a patched copy of `repo` under `work`.

    Fresh copies every time: a unit may write relative to its working
    directory, and a copy reused across submissions would hand the next one
    whatever the last one left behind.
    """
    before, after = work / "before", work / "after"
    for destination in (before, after):
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(repo, destination, ignore=IGNORED, symlinks=True)
    splice_tree(after, changed)
    return before, after


class Pair:
    """One worker holding both copies; `side(name)` addresses one of them."""

    def __init__(self, before_root: Path, after_root: Path, unit: str,
                 cases_source: str, work: Path, meter: str = "auto"):
        work.mkdir(parents=True, exist_ok=True)
        self.stderr_path = work / "worker.stderr"
        self._stderr = open(self.stderr_path, "w")
        # A fixed hash seed, so a set or dict iterates in a reproducible order.
        env = {**os.environ, "PYTHONHASHSEED": "0"}
        self.process = subprocess.Popen(
            [sys.executable, str(WORKER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr,
            text=True, bufsize=1, env=env,
        )
        self._send({"before_root": str(before_root), "after_root": str(after_root),
                    "before_workdir": str(work / "io-before"),
                    "after_workdir": str(work / "io-after"),
                    "unit": unit, "cases_source": cases_source, "meter": meter})
        ready = self._receive()
        if not ready.get("ok"):
            self.close()
            raise LoadError(ready.get("side", "before"), ready.get("stage", "start"),
                            ready.get("summary") or _last_line(ready.get("error", ""))
                            or self._tail())
        self.ready = ready
        if ready["before"]["cases"] != ready["after"]["cases"] or \
                ready["before"]["checks"] != ready["after"]["checks"]:
            self.close()
            raise LoadError("after", "cases",
                            "the two sides built different cases from the same source")

    @property
    def labels(self) -> list[str]:
        return self.ready["before"]["cases"]

    @property
    def check_labels(self) -> list[str]:
        return self.ready["before"]["checks"]

    @property
    def stubbed(self) -> list[str]:
        return sorted(set(self.ready["before"]["stubbed"]) | set(self.ready["after"]["stubbed"]))

    @property
    def skipped(self) -> list[str]:
        """Top-level statements skipped to load the unit's module, either side.

        As the original numbers them; the patched copy's line numbers shift with
        the repair, so its list adds only statements the original did not skip.
        """
        before = self.ready["before"]["skipped"]
        seen = {entry.split(" ", 2)[-1] for entry in before}
        return before + [entry for entry in self.ready["after"]["skipped"]
                         if entry.split(" ", 2)[-1] not in seen]

    def side(self, name: str) -> "_Side":
        return _Side(self, name)

    def ask(self, **request) -> dict:
        self._send(request)
        answer = self._receive()
        if not answer.get("ok"):
            raise WorkerError(answer.get("summary") or _last_line(answer.get("error", ""))
                              or self._tail(), stub_used=answer.get("stub_used", False))
        return answer

    def _send(self, payload: dict) -> None:
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

    def _receive(self) -> dict:
        line = self.process.stdout.readline()
        if not line:
            return {"ok": False, "stage": "start", "error": f"worker exited: {self._tail()}"}
        return json.loads(line)

    def _tail(self) -> str:
        try:
            self._stderr.flush()
            return _last_line(self.stderr_path.read_text(errors="replace"))
        except OSError:
            return ""

    def close(self) -> None:
        try:
            self.process.stdin.close()
            self.process.wait(timeout=10)
        except Exception:  # noqa: BLE001
            self.process.kill()
        self._stderr.close()


class _Side:
    """`pair.side("after").ask(op=...)` sends the request to that side."""

    def __init__(self, pair: Pair, name: str):
        self.pair, self.name = pair, name

    @property
    def ready(self) -> dict:
        return self.pair.ready[self.name]

    def ask(self, **request) -> dict:
        return self.pair.ask(side=self.name, **request)


def _last_line(text: str) -> str:
    lines = [line for line in (text or "").strip().splitlines() if line.strip()]
    return lines[-1].strip() if lines else ""
