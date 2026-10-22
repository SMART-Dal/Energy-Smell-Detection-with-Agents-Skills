#!/usr/bin/env python3
"""Ask for the inputs your repairs will be measured on, and see how far along they are.

    python inputs.py request src/app.py::Report.render src/parse.py::tokenize
    python inputs.py status

You do not write inputs. A generator outside this session writes them for each
unit you name: four measured inputs that make the unit do substantial and
different work, and a few edge inputs that are only checked for identical
behaviour. It keeps an input only if it runs on the original code and gives the
same output twice. The files appear in `.energy-inputs/`, read-only; read them
to see what your repair will face. After the session, every repair is measured
again on the generator's own copy of the same inputs.

`request` works once you have said step 1 is finished (`step.py done 1`): ask
for a unit's inputs in step 2, as soon as you know you will repair it. It
returns at once. Generating takes a minute or two, up to five for a hard unit,
all units at the same time, so carry on meanwhile;
verify.py waits (up to ten minutes) for any still being generated before it
measures anything. The inputs cannot be changed: editing the files changes
nothing that counts, because the re-measurement uses the generator's own copy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.inputs import DIRNAME, FAILED, MAX_REQUESTED, MAX_UNITS, READY, ask, read_status  # noqa: E402
from lib.progress import step_refusal  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inputs.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    request = sub.add_parser("request", help="ask for the inputs of these units")
    request.add_argument("units", nargs="+", metavar="path::qualname")
    sub.add_parser("status", help="which units are ready, still being generated, or failed")
    args = parser.parse_args(argv)

    if args.command == "request":
        refusal = step_refusal(1, "Asking for inputs")
        if refusal:
            print(refusal)
            return 2
        answer = ask({"op": "request", "units": args.units})
        if not answer.get("ok"):
            print(f"ERROR: {answer.get('error')}")
            return 2
        for unit in answer.get("accepted", []):
            print(f"  requested  {unit}")
        for unit in answer.get("again", []):
            print(f"  again      {unit}  (it failed before; generating it once more)")
        for unit in answer.get("already", []):
            print(f"  already    {unit}")
        for row in answer.get("rejected", []):
            print(f"  REJECTED   {row['unit']}: {row['why']}")
        print(f"\nGenerating in the background. A session has inputs for at most {MAX_UNITS} "
              f"units; one whose generation failed does not count, so another can take its "
              f"place, up to {MAX_REQUESTED} different units in all. Carry on; `inputs.py "
              f"status` shows progress, and verify.py waits for them before measuring.")
        return 1 if answer.get("rejected") else 0

    units = read_status(Path(DIRNAME))
    if not units:
        print("no inputs requested yet: `inputs.py request path::qualname ...`")
        return 0
    for unit, entry in sorted(units.items()):
        state = entry.get("state")
        line = f"  {state:<8} {unit}"
        if state == READY:
            line += f"  -> {DIRNAME}/{entry.get('file')}"
        elif state == FAILED:
            line += f"\n           {entry.get('reason')}"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
