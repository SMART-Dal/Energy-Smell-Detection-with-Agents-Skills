"""Where a run stands in the procedure, read from its findings.jsonl.

The steps run in order, each finished for every unit before the next begins:
step 1 lists the units, step 2 reads every one of them, step 3 decides every
unit that has suspicions, step 4 repairs and measures. Two things follow from
the records alone, with nothing else to trust:

  * the root-cause cards open once step 2 is done for every listed unit;
  * step 4 -- asking for inputs, measuring -- may begin once step 3 is done.

inputs.py and verify.py refuse to start step 4 before that, saying what is
missing, and the harness opens the cards on the same rule.
"""

from __future__ import annotations

import json
from pathlib import Path


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


def standing(records: list[dict]) -> dict:
    """The listed units, and which of them still lack a step-2 or step-3 record."""
    plans = [r for r in records if r.get("step") == 1]
    listed = [u for u in (plans[-1].get("will_examine") or []) if isinstance(u, str)] if plans else []
    read = {r.get("unit"): r for r in records if r.get("step") == 2}
    decided = {r.get("unit") for r in records if r.get("step") == 3}
    return {
        "planned": bool(plans),
        "listed": listed,
        "unread": [u for u in listed if u not in read],
        "undecided": [u for u in listed if u in read and read[u].get("suspicions") and u not in decided],
    }


def cards_open(records: list[dict]) -> bool:
    """Root-cause cards are for step 3 on: open once every listed unit is read.

    Nothing else opens them -- not even a submission, which an agent could
    write early for no other reason."""
    s = standing(records)
    return s["planned"] and bool(s["listed"]) and not s["unread"]


def step4_gaps(findings: Path) -> list[str]:
    """What has to be written before step 4 may begin; empty when nothing does."""
    try:
        records = parse_records(Path(findings).read_text(errors="replace"))
    except OSError:
        return ["there is no findings.jsonl in the repository root yet"]
    s = standing(records)
    if not s["planned"]:
        return ["findings.jsonl has no step-1 record listing the units you examine"]
    gaps = []
    if s["unread"]:
        gaps.append(f"no step-2 record yet for {len(s['unread'])} unit(s) on your step-1 list: "
                    + ", ".join(s["unread"]))
    if s["undecided"]:
        gaps.append(f"no step-3 record yet for {len(s['undecided'])} unit(s) with suspicions: "
                    + ", ".join(s["undecided"]))
    return gaps


def gaps_message(gaps: list[str]) -> str:
    return ("Step 4 begins once steps 2 and 3 are done for every unit on your latest step-1 "
            "list. Still missing:\n" + "\n".join(f"  - {g}" for g in gaps) +
            "\nWrite those records to findings.jsonl in the repository root, or drop units you "
            "will not examine by appending a new step-1 record, then run this again.")
