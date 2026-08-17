#!/usr/bin/env python3
"""Run every analyzer's tests.

    python tests/rules/run.py                      all of them
    python tests/rules/run.py string_concat_in_loop
    python tests/rules/run.py --list-uncovered

One directory per rule, each holding `test_cases.py` and `test_main.py`. This
walks them, runs each, and reports which analyzers still have no tests at all --
because a suite that passes because nobody wrote the test is the failure mode
worth guarding against.

Each `test_main.py` is also runnable on its own, which is what you want while
fixing one rule.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _harness import ALL_RULES, RuleTestFailure  # noqa: E402


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"_test_{path.parent.name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_one(directory: Path) -> tuple[bool, str]:
    """Run every `test_*` function in one rule's test_main.py."""
    main = directory / "test_main.py"
    if not main.exists():
        return False, f"{directory.name}: no test_main.py"
    try:
        module = load(main)
    except Exception:
        return False, f"{directory.name}: test_main.py failed to import\n{traceback.format_exc()}"

    tests = [v for k, v in vars(module).items() if k.startswith("test_") and callable(v)]
    if not tests:
        return False, f"{directory.name}: test_main.py defines no test_ functions"

    for test in tests:
        try:
            test()
        except RuleTestFailure as exc:
            return False, str(exc)
        except Exception:
            return False, f"{directory.name}::{test.__name__} raised\n{traceback.format_exc()}"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("rules", nargs="*", help="rule names; default is all")
    parser.add_argument("--list-uncovered", action="store_true")
    args = parser.parse_args(argv)

    known = {rule.__name__ for rule in ALL_RULES}
    tested = {d.name for d in HERE.iterdir() if d.is_dir() and not d.name.startswith("_")}
    uncovered = sorted(known - tested)
    stray = sorted(tested - known)

    if args.list_uncovered:
        print("\n".join(uncovered) or "every analyzer has a test directory")
        return 0

    wanted = sorted(args.rules) if args.rules else sorted(tested)
    unknown = [name for name in wanted if name not in tested]
    if unknown:
        parser.error(f"no test directory for: {', '.join(unknown)}")

    failures = []
    for name in wanted:
        ok, message = run_one(HERE / name)
        if not ok:
            failures.append(message)

    for message in failures:
        print(message)
        print()

    for name in stray:
        print(f"stray: tests/rules/{name}/ matches no analyzer")

    print(f"{len(wanted)} rule(s) tested, {len(failures)} failing, "
          f"{len(uncovered)} analyzer(s) with no tests")
    if uncovered and not args.rules:
        print("  no tests: " + ", ".join(uncovered))
    return 1 if failures or stray else 0


if __name__ == "__main__":
    sys.exit(main())
