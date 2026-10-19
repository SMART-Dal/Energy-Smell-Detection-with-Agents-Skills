"""Where a run stands in the procedure.

Every step is finished for every unit the agent examines before the next one
begins, and the agent says when it finishes one -- `step.py done 2`, `step.py
done 3` -- to the input service, which keeps the findings as they are at that
moment (tools/inputs/recorder.py). Step 4 -- asking for inputs, measuring -- may
begin once step 3 is said to be finished; inputs.py and verify.py ask before
they start.
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


def step4_refusal() -> str | None:
    """None when step 4 may begin; otherwise what the agent should do first."""
    answer = ask({"op": "steps"}, timeout=10)
    if not answer.get("ok"):
        return None                           # no service: nothing to enforce here
    if 3 in (answer.get("done") or []):
        return None
    return ("Step 4 begins once step 3 is finished, and you say so: run\n"
            "    python $SKILL/scripts/step.py done 3\n"
            "(it also finishes step 2, if you have not said so yet), then run this again.")
