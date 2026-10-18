#!/usr/bin/env python3
"""Generate inputs for a list of units at once, the way the service would: a pilot.

    python batch.py UNITS.tsv --pristine DIR --venvs DIR --out DIR --key FILE [--cache DIR]

UNITS.tsv has one `repo<TAB>path::qualname` per line. Each unit runs generate.py
under its repository's venv (`--venvs/<repo>/venv/bin/python`) against its
pristine clone (`--pristine/<repo>`), all units in parallel, and a table of the
outcomes is printed at the end. Without `--cache` every unit is generated fresh.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src"))

from lib.inputs import file_name  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("units", type=Path)
    parser.add_argument("--pristine", type=Path, required=True)
    parser.add_argument("--venvs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()

    rows = [line.rstrip("\n").split("\t") for line in args.units.read_text().splitlines()
            if line.strip()]

    def one(row):
        repo, unit = row
        out = args.out / repo / file_name(unit)[:-3]
        out.mkdir(parents=True, exist_ok=True)
        command = [str(args.venvs / repo / "venv" / "bin" / "python"), str(HERE / "generate.py"),
                   str(args.pristine / repo), unit, str(out), "--key", str(args.key)]
        if args.cache:
            command += ["--cache", str(args.cache)]
        done = subprocess.run(command, capture_output=True, text=True, timeout=1200)
        (out / "stderr.log").write_text(done.stderr)
        last = next((l for l in reversed(done.stdout.splitlines()) if l.startswith("{")), None)
        return repo, unit, json.loads(last) if last else {"crash": done.stderr[-300:]}

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(rows)) as pool:
        results = list(pool.map(one, rows))
    print(f"{len(rows)} units in {time.monotonic() - started:.0f} s\n")
    total = 0.0
    for repo, unit, r in results:
        total += r.get("cost") or 0
        state = ("CRASH " + r["crash"][-120:]) if "crash" in r else \
            ("ready" if r.get("ready") else "FAILED: " + (r.get("reason") or "")[:150])
        print(f"{repo:<22} {unit[-55:]:<55} {state}")
        if "crash" not in r and not r.get("cached"):
            print(f"{'':<22}   calls {r.get('llm_s')} s, rounds {r.get('rounds')}, "
                  f"{r.get('s')} s total, ${r.get('cost')}"
                  + (f", errors {r.get('errors')}" if r.get("errors") else ""))
    print(f"\ntotal reported cost ${total:.3f}")
    (args.out / "summary.json").write_text(json.dumps(
        [{"repo": repo, "unit": unit, **r} for repo, unit, r in results], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
