"""Where a run stands in the procedure.

Each step writes its own file, and the agent says when it finishes one --
`step.py done N` -- to the input service, which keeps the file as it is then
and makes it read-only (tools/inputs/steps.py). Step 4 -- asking for inputs,
measuring -- runs between `done 3` and `done 4`, and inputs may be asked for
from `done 2`; inputs.py and verify.py ask before they start.
"""

from __future__ import annotations

import json

from .inputs import ask


def parse_records(text: str) -> list[dict]:
    """Every JSON object in the text, one per line or spread over several."""
    decoder, out, i = json.JSONDecoder(), [], 0
    while i < len(text):
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text):
            break
        try:
            value, i = decoder.raw_decode(text, i)
        except ValueError:
            nl = text.find("\n", i)          # an unreadable line: skip it, keep the rest
            i = len(text) if nl < 0 else nl + 1
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


def step_refusal(after: int, what: str) -> str | None:
    """None when `what` may run -- from `done <after>` until `done 4`; otherwise
    what the agent should do first."""
    answer = ask({"op": "steps"}, timeout=10)
    if not answer.get("ok"):
        return None                           # no service: nothing to enforce here
    done = answer.get("done") or []
    if 4 in done:
        return "Step 4 is finished (`step.py done 4`): its files are read-only, and nothing more is requested or measured."
    if after in done:
        return None
    earlier = [f"`done {n}`" for n in range(1, after) if n not in done]
    # Not "run done N now": an agent told that finished step 2 on the spot,
    # skipping its rules and its sweep, just to ask for inputs a step early.
    return (f"{what} belongs to step {after + 1}, so it is not open yet. Carry on with "
            f"step {after}: finish all of it, every sub-step in SKILL.md, and only then "
            f"say so with `python $SKILL/scripts/step.py done {after}`"
            + (f" (after {' and '.join(earlier)})" if earlier else "") + ". Run this again after that.")
