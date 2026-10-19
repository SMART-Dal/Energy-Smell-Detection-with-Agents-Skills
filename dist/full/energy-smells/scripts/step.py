#!/usr/bin/env python3
"""Say that a step is finished.

    python step.py done 2      step 2 is finished: its records are kept as they are now
    python step.py done 3      step 3 is finished: step 4 may begin
    python step.py status      which steps are finished

Each step is finished for every unit you examine before the next one begins.
When you finish one, say so here: what findings.jsonl holds at that moment is
kept, outside this session, as that step's output. Records you write afterwards
are kept too, with the time they were written.

After `done 2`, the root-cause cards are open. After `done 3`, inputs.py and
verify.py start step 4.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.inputs import ask  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="step.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    done = sub.add_parser("done", help="say that a step is finished")
    done.add_argument("step", type=int, choices=(2, 3))
    sub.add_parser("status", help="which steps are finished")
    args = parser.parse_args(argv)

    if args.command == "status":
        answer = ask({"op": "steps"})
        if not answer.get("ok"):
            print(f"ERROR: {answer.get('error')}")
            return 2
        finished = answer.get("done") or []
        print("finished: " + (", ".join(f"step {n}" for n in finished) if finished else "none yet"))
        return 0

    answer = ask({"op": "done", "step": args.step})
    if not answer.get("ok"):
        print(f"ERROR: {answer.get('error')}")
        return 2
    print(answer.get("message", f"step {args.step} recorded as finished"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
