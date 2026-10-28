#!/usr/bin/env python3
"""Size of each subject repository, at the commit the runs analyzed, for the paper.

    python experiment/lib/repo_stats.py sample-apps dx-toolkit community
    python experiment/lib/repo_stats.py --stars sample-apps dx-toolkit community

Reads the pristine clones in $ENERGY_EXP/pristine (default ~/energy-exp/pristine),
the same copies every run started from, and checks that each one is at the
commit repos.tsv names. Every number is computed here, so a table in the paper
can cite this command instead of a hand count. The definitions:

  files   Python files tracked by git at that commit (`git ls-files '*.py'`).
  units   function and method definitions, `def` and `async def`, nested ones
          included, counted from Python's own parse of each file. A file that
          does not parse adds none; it is named on stderr.
  lines   lines that are not blank and are not only a comment (a line whose
          first non-space character is `#`). Docstrings count as lines.
  tests   the same three counts for test files only: a file under a directory
          named `test` or `tests`, or named `test_*.py` or `*_test.py`.
  stars   GitHub's stargazers count, fetched when the command runs (`--stars`),
          with the date it was fetched. Not the count at collection time.
"""

from __future__ import annotations

import argparse
import ast
import csv
import datetime
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path, PurePosixPath

HARNESS = Path(__file__).resolve().parent.parent
PRISTINE = Path(os.environ.get("ENERGY_EXP", Path.home() / "energy-exp")) / "pristine"


def is_test(path: str) -> bool:
    parts = PurePosixPath(path).parts
    name = parts[-1]
    return any(part in ("test", "tests") for part in parts[:-1]) or \
        name.startswith("test_") or name.endswith("_test.py")


def count(root: Path, files: list[str]) -> dict:
    units = lines = 0
    unparsable = []
    for name in files:
        source = (root / name).read_bytes().decode("utf-8", "replace")
        lines += sum(1 for line in source.splitlines()
                     if line.strip() and not line.strip().startswith("#"))
        try:
            tree = ast.parse(source)
        except SyntaxError:
            unparsable.append(name)
            continue
        units += sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     for node in ast.walk(tree))
    return {"files": len(files), "units": units, "lines": lines, "unparsable": unparsable}


def stars(slug: str) -> int | None:
    request = urllib.request.Request(f"https://api.github.com/repos/{slug}",
                                     headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response).get("stargazers_count")
    except OSError as exc:
        print(f"{slug}: stars not fetched ({exc})", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repos", nargs="+", help="names as in repos.tsv")
    parser.add_argument("--stars", action="store_true", help="also fetch GitHub's star count")
    args = parser.parse_args()

    listed = {row[0]: row for row in csv.reader(open(HARNESS / "repos.tsv"), delimiter="\t") if row}
    fetched = datetime.date.today().isoformat()
    rows = []
    for name in args.repos:
        if name not in listed:
            print(f"{name}: not in repos.tsv", file=sys.stderr)
            return 2
        slug, commit = listed[name][1], listed[name][2]
        root = PRISTINE / name
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        if head != commit:
            print(f"{name}: the clone is at {head}, repos.tsv says {commit}", file=sys.stderr)
            return 1
        files = subprocess.run(["git", "-C", str(root), "ls-files", "*.py"],
                               capture_output=True, text=True, check=True).stdout.split()
        every = count(root, files)
        tests = count(root, [f for f in files if is_test(f)])
        for path in every["unparsable"]:
            print(f"{name}: {path} does not parse; its units are not counted", file=sys.stderr)
        rows.append({"repo": slug, "commit": commit[:7], **{k: every[k] for k in ("files", "units", "lines")},
                     "test_files": tests["files"], "test_units": tests["units"], "test_lines": tests["lines"],
                     "stars": stars(slug) if args.stars else None})

    columns = ["repo", "commit", "files", "units", "lines", "test_files", "test_units", "test_lines"]
    if args.stars:
        columns.append("stars")
        print(f"stars fetched {fetched}", file=sys.stderr)
    writer = csv.DictWriter(sys.stdout, fieldnames=columns, delimiter="\t", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
