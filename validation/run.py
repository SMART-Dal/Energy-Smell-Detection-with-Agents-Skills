#!/usr/bin/env python3
"""Run a directory of case files through the verifier and tabulate the verdicts.

    python validation/run.py samples          # Javad's 84 hand-written pairs
    python validation/run.py taxonomy         # 2-3 scenarios per root cause
    python validation/run.py samples --only SumTopK

Results land in `validation/results/<suite>.jsonl`, one line per case file,
appended as each finishes.  The batch is resumable: a case file already present
in the jsonl is skipped, so an interrupted run costs only the case it was on.

Each case file runs in its own subprocess.  That is not tidiness -- these are
arbitrary functions at benchmark sizes, and a few of them allocate gigabytes or
recurse to the stack limit.  In-process, one bad sample takes the batch with it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "src" / "verify.py"
"""The authored verifier, not a built arm's copy.

Every arm ships an identical verify.py, so which one runs cannot change a
verdict -- but running the source keeps validation honest about what it is
testing, and works before `python -m build` has been run at all.
"""
RESULTS = ROOT / "validation" / "results"

TIMEOUT_S = 480
"""Wall-clock ceiling for one case file.

Derived from the measurement parameters rather than picked. One measured
subprocess costs `WARMUP_SECONDS + reps x 2 x TARGET_WINDOW_S`, which at the
current settings is 10 + 9 x 2 x 3 = 64 s. A case file spends that once per
case and once more for the canary on the deciding case, so an n-case file
costs about `(n + 1) x 64` s: 192 s for two cases, 256 s for three, 384 s for
five. This ceiling clears the largest of those with room for the equivalence
and sizing stages on top.

Change any of those three constants and recompute this one. Set it below the
budget and the suite reports `timeout` for case files that are working
perfectly -- at 240 s, every three-case file in the taxonomy suite would fail,
which is most of it.

What it is still for: a sample whose inputs were sized for a different kind of
experiment, which is more useful reported as `timeout` than left to block the
queue.
"""


def run_one(case_path: Path, python: str) -> dict:
    """Verify one case file, turning every failure mode into a result row."""
    started = time.time()
    try:
        completed = subprocess.run(
            [python, str(VERIFY), str(case_path), "--json"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        return _row(case_path, "timeout", f"exceeded {TIMEOUT_S}s", started)

    try:
        payload = json.loads(completed.stdout)
    except ValueError:
        # verify.py exits non-zero with a plain message for a malformed case
        # file or a failed equivalence check; both are real results.
        message = (completed.stderr or completed.stdout or "no output").strip()
        return _row(case_path, "error", message.splitlines()[-1][:200], started)

    payload["case_file"] = str(case_path.relative_to(ROOT))
    payload["seconds"] = round(time.time() - started, 1)
    return payload


def _row(case_path: Path, status: str, reason: str, started: float) -> dict:
    return {
        "case_file": str(case_path.relative_to(ROOT)),
        "status": status,
        "reason": reason,
        "seconds": round(time.time() - started, 1),
    }


def _drop(log: Path, root: Path, stems: list[str], prune: bool) -> None:
    """Remove stored rows so the next pass measures them again.

    A row is dropped when its stem matches one of `stems`, or -- with `prune` --
    when the case file behind it is gone. Everything else is rewritten
    untouched, which is what makes a re-measurement cost minutes instead of the
    hours a `--restart` would.
    """
    kept, dropped = [], 0
    for line in log.read_text().splitlines():
        if not line:
            continue
        row = json.loads(line)
        path = root / row["case_file"]
        if any(stem in path.stem for stem in stems) or (prune and not path.exists()):
            dropped += 1
            continue
        kept.append(line)
    log.write_text("".join(f"{line}\n" for line in kept))
    print(f"dropped {dropped} stored rows, {len(kept)} kept", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", help="subdirectory of validation/ to run")
    parser.add_argument("--only", default="", help="substring filter on the filename")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--restart", action="store_true", help="discard earlier results")
    parser.add_argument(
        "--redo",
        default="",
        help="comma-separated stems to re-measure: their stored rows are dropped "
             "first, so only those are run again. Use this rather than --restart "
             "when a handful of case files changed -- a full suite is hours.",
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="drop stored rows whose case file no longer exists, then continue",
    )
    args = parser.parse_args(argv)

    suite = ROOT / "validation" / args.suite
    cases = sorted(p for p in suite.glob("*.py") if not p.name.startswith("_"))
    if args.only:
        cases = [p for p in cases if args.only.lower() in p.name.lower()]

    RESULTS.mkdir(parents=True, exist_ok=True)
    log = RESULTS / f"{args.suite}.jsonl"
    if args.restart and log.exists():
        log.unlink()

    if log.exists() and (args.redo or args.prune):
        _drop(log, ROOT, [s for s in args.redo.split(",") if s], args.prune)

    done = set()
    if log.exists():
        done = {json.loads(line)["case_file"] for line in log.read_text().splitlines() if line}

    todo = [p for p in cases if str(p.relative_to(ROOT)) not in done]
    print(f"{len(cases)} case files, {len(done)} already done, {len(todo)} to run", flush=True)

    for index, case_path in enumerate(todo, 1):
        result = run_one(case_path, args.python)
        with log.open("a") as handle:
            handle.write(json.dumps(result) + "\n")
        print(
            f"[{index}/{len(todo)}] {result['status']:<10} "
            f"{result.get('energy_saved_pct', 0):+7.1f}%  "
            f"{case_path.stem}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
