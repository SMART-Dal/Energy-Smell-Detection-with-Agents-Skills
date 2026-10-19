#!/usr/bin/env python3
"""Generate an agent's inputs outside its session, while it carries on working.

    <the run's venv python> service.py --repo-name NAME --pristine DIR --repo DIR \\
        --socket PATH --cache DIR --out DIR --key FILE --work DIR

run_all.sh starts this before the agent and finishes it after. It reads the key,
copies the pristine clone, and opens the cache and our copy of the inputs before
the harness locks ~/energy-exp, and never puts the key anywhere the agent can
read: not in the environment, not in arguments, not on disk outside the lock.

The agent asks through `inputs.py`, one JSON line per connection on the socket:

    {"op": "request", "units": [...]}  answered at once; generation runs in threads
    {"op": "status"}                   every requested unit and its state
    {"op": "finish", "wait_s": N}      waits for what is pending, answers, and exits

Each unit's inputs go to two places with the same layout -- `status.json` and
one file per unit: the repository's `.energy-inputs/`, read-only, for the
agent; and `--out`, where the agent cannot reach, which is what the review
measures with. A unit generated once for a repository is cached and reused by
every later run -- every arm and every model measures that unit on the same
inputs.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import signal
import socket
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate as gen  # noqa: E402
from recorder import Recorder  # noqa: E402
from lib.inputs import DIRNAME, FAILED, MAX_UNITS, PENDING, READY, STATUS, file_name  # noqa: E402
from lib.splice import split_name  # noqa: E402

VALIDATIONS_AT_ONCE = 8
"""Candidates executing at the same time. The LLM calls all run at once; executing
twenty sets of candidates at once, each in a worker holding two copies of the
repository, is where memory and the agent's own work would suffer."""


class Service:
    def __init__(self, args):
        self.repo_name = args.repo_name
        self.key = args.key.read_text().strip()
        self.work = args.work.resolve()
        self.work.mkdir(parents=True, exist_ok=True)
        self.pristine = self.work / "pristine" / args.repo_name
        if self.pristine.exists():
            shutil.rmtree(self.pristine)
        shutil.copytree(args.pristine, self.pristine, symlinks=True,
                        ignore=shutil.ignore_patterns(".git"))
        self.cache = gen.Store(args.cache)
        self.out = gen.Store(args.out)
        self.agent_dir = args.repo.resolve() / DIRNAME
        self.agent_dir.mkdir(exist_ok=True)
        self.units: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=MAX_UNITS)
        self.futures = []
        self.closing = False
        gen.VALIDATION_SLOTS = threading.BoundedSemaphore(VALIDATIONS_AT_ONCE)
        self._publish_status()
        # Every version of findings.jsonl and submissions.jsonl, and the gate on
        # the root-cause cards: see recorder.py.
        self.recorder = None
        if args.record:
            self.recorder = Recorder(args.repo.resolve(), gen.Store(args.record),
                                     args.cards.resolve() if args.cards else None)
            self.recorder.start()

    # -- what the agent sees, and what we keep -----------------------------

    def _write_agent(self, name: str, text: str) -> None:
        """Into `.energy-inputs/`, read-only, the directory read-only between writes."""
        os.chmod(self.agent_dir, 0o755)
        try:
            target = self.agent_dir / name
            tmp = self.agent_dir / f".{name}.tmp"
            tmp.write_text(text)
            os.chmod(tmp, 0o444)
            os.replace(tmp, target)
        finally:
            os.chmod(self.agent_dir, 0o555)

    def _publish_status(self) -> None:
        text = json.dumps({"units": self.units, "updated": time.time()}, indent=1)
        self._write_agent(STATUS, text)
        self.out.write(STATUS, text)

    def _log(self, row: dict) -> None:
        line = json.dumps(row) + "\n"
        with self.lock:
            existing = self.out.read("_generation/log.jsonl") or ""
            self.out.write("_generation/log.jsonl", existing + line)

    # -- requests ------------------------------------------------------------

    def _check_unit(self, unit) -> str | None:
        if not isinstance(unit, str):
            return "not a `path::qualname` string"
        try:
            path, qualname = split_name(unit)
        except ValueError as exc:
            return str(exc)
        file = self.pristine / path
        if not file.is_file():
            return f"no file {path} in the repository"
        try:
            tree = ast.parse(file.read_text(errors="replace"))
            node, _ = gen.find_node(tree, qualname)
        except KeyError:
            return f"no function or method {qualname} in {path}"
        except (SyntaxError, ValueError) as exc:
            return f"{path} does not parse: {exc}"
        if isinstance(node, ast.ClassDef):
            return f"{qualname} is a class; name one of its methods"
        # A function defined inside another function exists only while the outer
        # one runs, so nothing can call it on its own: the scanner ranked one first
        # in the pilot, and it failed only after generation had been paid for.
        parts = qualname.split(".")
        for depth in range(1, len(parts)):
            outer, _ = gen.find_node(tree, ".".join(parts[:depth]))
            if isinstance(outer, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return (f"{parts[-1]} is defined inside {'.'.join(parts[:depth])}, so it cannot "
                        f"be called on its own; request {path}::{'.'.join(parts[:depth])}, the "
                        f"function that contains it")
        return None

    def request(self, units) -> dict:
        if not isinstance(units, list):
            return {"ok": False, "error": "`units` must be a list of path::qualname strings"}
        accepted, already, rejected = [], [], []
        with self.lock:
            if self.closing:
                return {"ok": False, "error": "the session is over; no more requests"}
            for unit in dict.fromkeys(units):
                problem = self._check_unit(unit)
                if problem:
                    rejected.append({"unit": unit, "why": problem})
                elif unit in self.units:
                    already.append(unit)
                elif len(self.units) >= MAX_UNITS:
                    rejected.append({"unit": unit, "why": f"at most {MAX_UNITS} units a session"})
                else:
                    self.units[unit] = {"state": PENDING, "requested": time.time()}
                    self.futures.append(self.pool.submit(self._job, unit))
                    accepted.append(unit)
            if accepted:
                self._publish_status()
        return {"ok": True, "accepted": accepted, "already": already, "rejected": rejected}

    def _job(self, unit: str) -> None:
        started = time.monotonic()
        slug = file_name(unit)[:-3]
        row = {"unit": unit, "cached": False}
        try:
            key = gen.cache_key(self.pristine, self.repo_name, unit)
            source = self.cache.read(f"{key}/cases.py")
            if source:
                row.update(cached=True, ready=True, cost=0.0)
                reason = ""
            else:
                outcome = gen.generate(
                    self.pristine, unit, self.work / "jobs" / slug, self.key,
                    record=lambda name, text: self.out.write(f"_generation/{slug}/{name}", text))
                report = json.dumps(outcome.report, indent=1)
                self.out.write(f"_generation/{slug}/report.json", report)
                source, reason = outcome.source, outcome.reason
                r = outcome.report
                row.update(ready=outcome.ready, cost=r.get("cost"), rounds=len(r.get("rounds", [])),
                           calls=len(r.get("calls", [])),
                           timeouts=sum(1 for c in r.get("calls", []) if c.get("error")))
                if outcome.ready:
                    self.cache.write(f"{key}/cases.py", source)
                    self.cache.write(f"{key}/report.json", report)
        except Exception as exc:  # noqa: BLE001 -- a broken job fails its unit, never the service
            source, reason = None, f"the generator failed: {type(exc).__name__}: {exc}"
            row.update(ready=False)
        row.update(seconds=round(time.monotonic() - started, 1), reason=reason or None)
        with self.lock:
            if source:
                self.out.write(file_name(unit), source)
                self._write_agent(file_name(unit), source)
                self.units[unit] = {"state": READY, "file": file_name(unit)}
            else:
                self.units[unit] = {"state": FAILED, "reason": reason}
            self._publish_status()
        self._log(row)

    def status(self) -> dict:
        with self.lock:
            return {"ok": True, "units": dict(self.units)}

    def finish(self, wait_s: float) -> dict:
        with self.lock:
            self.closing = True
            futures = list(self.futures)
        deadline = time.monotonic() + wait_s
        for f in futures:
            try:
                f.result(timeout=max(0.0, deadline - time.monotonic()))
            except Exception:  # noqa: BLE001 -- a timeout or a failed job; reported below
                pass
        with self.lock:
            left = sorted(u for u, s in self.units.items() if s["state"] == PENDING)
            for unit in left:
                self.units[unit] = {"state": FAILED, "reason": "still generating when the session ended"}
            self._publish_status()
        recorded = self.recorder.finish() if self.recorder else {}
        return {"ok": True, "pending_at_end": left, **recorded}


def serve(service: Service, path: Path) -> None:
    if path.exists():
        path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    os.chmod(path, 0o600)
    server.listen(16)
    print("ready", flush=True)
    done = threading.Event()

    def handle(conn: socket.socket) -> None:
        with conn:
            try:
                data = b""
                while not data.endswith(b"\n"):
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    data += chunk
                request = json.loads(data or b"{}")
                op = request.get("op")
                if op == "request":
                    answer = service.request(request.get("units"))
                elif op == "status":
                    answer = service.status()
                elif op == "done" and service.recorder is not None and request.get("step") in (2, 3):
                    answer = {"ok": True, **service.recorder.declare(int(request["step"]))}
                elif op == "steps":
                    answer = {"ok": True, "done": list(service.recorder.done) if service.recorder else []}
                elif op == "finish":
                    answer = service.finish(float(request.get("wait_s", 600)))
                    done.set()
                else:
                    answer = {"ok": False, "error": f"unknown op {op!r}"}
            except Exception as exc:  # noqa: BLE001
                answer = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            try:
                conn.sendall((json.dumps(answer) + "\n").encode())
            except OSError:
                pass
        if done.is_set():
            server.close()

    server.settimeout(1.0)
    while not done.is_set():
        try:
            conn, _ = server.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        threading.Thread(target=handle, args=(conn,), daemon=True).start()
    path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--pristine", type=Path, required=True, help="the pristine clone")
    parser.add_argument("--repo", type=Path, required=True, help="the agent's copy of the repository")
    parser.add_argument("--socket", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="our copy of the inputs")
    parser.add_argument("--key", type=Path, required=True, help="file holding the OpenRouter key")
    parser.add_argument("--work", type=Path, required=True, help="scratch space for candidates")
    parser.add_argument("--record", type=Path,
                        help="where every version of the agent's findings and submissions is kept")
    parser.add_argument("--cards", type=Path,
                        help="the skill's root-cause cards, opened only when the protocol allows")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
    serve(Service(args), args.socket)
    os._exit(0)  # pool threads of an abandoned job must not keep the process alive


if __name__ == "__main__":
    sys.exit(main())
