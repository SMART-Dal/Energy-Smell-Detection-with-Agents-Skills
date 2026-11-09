"""Where a run stands in the procedure.

Each step writes its own file, and the agent says when it finishes one --
`step.py done N` -- to the input service, which keeps the file as it is then
and makes it read-only (tools/inputs/steps.py). Step 3 -- asking for inputs
and measuring -- runs between `done 2` and `done 3`; inputs.py and verify.py
ask before they start.
"""

from __future__ import annotations

import json

from .inputs import ask

LAST_STEP = 3
"""The last step that writes a file; `done 3` closes the run's measuring."""

VERDICTS = ("confirmed", "partial", "mixed", "regressed", "negligible")
"""A measured result about the repair. Every other status says why there is none."""

MAX_REPAIRS = 20
"""Repairs one session measures to a verdict: a limit, not a target. A repair
that gets no verdict (`no_inputs`, `not_equivalent`, ...) takes no place; one
that gets a verdict keeps its place, deleted or edited (verify.py, review.py)."""


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
    """None when `what` may run -- from `done <after>` until `done LAST_STEP`;
    otherwise what the agent should do first."""
    answer = ask({"op": "steps"}, timeout=10)
    if not answer.get("ok"):
        return None                           # no service: nothing to enforce here
    done = answer.get("done") or []
    if LAST_STEP in done:
        return (f"Step {LAST_STEP} is finished (`step.py done {LAST_STEP}`): its files are "
                f"read-only, and nothing more is requested or measured.")
    if after in done:
        return None
    earlier = [f"`done {n}`" for n in range(1, after) if n not in done]
    # Not "run done N now": an agent told that once finished a step on the spot,
    # skipping the rest of it, just to ask for inputs a step early.
    return (f"{what} belongs to step {after + 1}, so it is not open yet. Carry on with "
            f"step {after}: finish all of it, everything SKILL.md asks of it, and only then "
            f"say so with `python $SKILL/scripts/step.py done {after}`"
            + (f" (after {' and '.join(earlier)})" if earlier else "") + ". Run this again after that.")
