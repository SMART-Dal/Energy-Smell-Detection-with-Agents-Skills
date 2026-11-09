#!/usr/bin/env python3
"""Say that a step is finished.

    python step.py done 1      step1.jsonl is finished
    python step.py done 2      step2.jsonl is finished
    python step.py done 3      submissions.jsonl and step3.jsonl are finished
    python step.py status      which steps are finished

Each step writes its own file in the repository's root, and you may write and
rewrite it as you like while the step is open. When the step is finished, say
so here: the file is kept, outside this session, as that step's output, and
becomes read-only. Steps finish in order.
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
    done.add_argument("step", type=int, choices=(1, 2, 3))
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
