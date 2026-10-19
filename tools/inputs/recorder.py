"""Keep every version of what the agent writes, and open the root-cause cards only when the protocol allows.

Runs inside the input service, beside the agent, for the whole session. It
watches the two files the agent writes in the repository's root and is never
seen by it:

  * **Every version is kept.** Each line added to, changed in or removed from
    `findings.jsonl` and `submissions.jsonl` is appended, timestamped, to
    `events.jsonl` in our own directory, which the agent cannot reach. A step
    record is kept as it was first written, whatever happens to it later, and a
    repair the agent deletes after a bad verdict is still on record --
    `submissions_all.jsonl` holds the final file plus every line it lost, and
    the review measures that. The agent's file is never touched.

  * **Root-cause cards follow the protocol.** Step 2 is to be written before any
    root-cause card is opened; step 3 opens them. Steps 2 and 3 alternate unit
    by unit, so the cards' directory is opened and closed from the agent's own
    records: open while some unit has a step-2 record and no step-3 record yet,
    or once every unit on the step-1 list has been read, or once repairs exist;
    closed otherwise. No card is locked before step 1 is written, and none is
    ever closed during step 4.

No permission stops an agent running as the same user from editing its own
files or from `chmod`; what this guarantees is that nothing it does is lost,
and the run's audit flags any `chmod`.
"""

from __future__ import annotations

import difflib
import json
import os
import threading
import time
from pathlib import Path

FILES = ("findings.jsonl", "submissions.jsonl")


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
            nl = text.find("\n", i)       # an unreadable line: skip it, keep the rest
            i = len(text) if nl < 0 else nl + 1
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


def cards_open(records: list[dict], has_submissions: bool) -> bool:
    """Whether the protocol lets the agent read root-cause cards right now."""
    if has_submissions:
        return True                                   # step 4: repairs use the cards
    plans = [r for r in records if r.get("step") == 1]
    if not plans:
        return False
    listed = [u for u in (plans[-1].get("will_examine") or []) if isinstance(u, str)]
    read = {r.get("unit"): r for r in records if r.get("step") == 2}
    decided = {r.get("unit") for r in records if r.get("step") == 3}
    if any(r.get("suspicions") and unit not in decided for unit, r in read.items()):
        return True                                   # a unit is between its step 2 and step 3
    return bool(listed) and all(unit in read for unit in listed)  # all read: on to step 4


class Recorder(threading.Thread):
    def __init__(self, repo: Path, store, cards: Path | None, poll_s: float = 0.25):
        super().__init__(daemon=True)
        self.repo = Path(repo)
        self.store = store
        self.cards = Path(cards) if cards else None
        self.poll_s = poll_s
        self.seen: dict[str, tuple] = {name: (None, None) for name in FILES}
        self.lines: dict[str, list[str]] = {name: [] for name in FILES}
        self.ever: dict[str, dict] = {}               # submission id -> last version seen
        self.open: bool | None = None
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self._gate(False)

    def run(self) -> None:
        while not self.stopping.is_set():
            self.poll()
            self.stopping.wait(self.poll_s)

    def poll(self) -> None:
        with self.lock:
            changed = False
            for name in FILES:
                path = self.repo / name
                try:
                    st = path.stat()
                    key = (st.st_mtime_ns, st.st_size)
                except OSError:
                    key = (None, None)
                if key == self.seen[name]:
                    continue
                self.seen[name] = key
                try:
                    text = path.read_text(errors="replace") if key[0] is not None else ""
                except OSError:
                    continue
                self._diff(name, text.splitlines())
                changed = True
            if changed:
                findings = parse_records("\n".join(self.lines["findings.jsonl"]))
                has_subs = any(line.strip() for line in self.lines["submissions.jsonl"])
                self._gate(cards_open(findings, has_subs))

    def _diff(self, name: str, new: list[str]) -> None:
        old = self.lines[name]
        now = time.time()
        rows = []
        for op, a1, a2, b1, b2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            if op == "insert":
                rows += [{"t": now, "file": name, "event": "added", "line": b1 + k + 1,
                          "text": new[b1 + k]} for k in range(b2 - b1)]
            elif op == "delete":
                rows += [{"t": now, "file": name, "event": "removed", "line": a1 + k + 1,
                          "was": old[a1 + k]} for k in range(a2 - a1)]
            else:                                     # replace: pair them up, the rest add or remove
                for k in range(max(a2 - a1, b2 - b1)):
                    row = {"t": now, "file": name, "line": b1 + k + 1}
                    if k < a2 - a1 and k < b2 - b1:
                        row.update(event="changed", text=new[b1 + k], was=old[a1 + k])
                    elif k < b2 - b1:
                        row.update(event="added", text=new[b1 + k])
                    else:
                        row.update(event="removed", was=old[a1 + k], line=a1 + k + 1)
                    rows.append(row)
        self.lines[name] = new
        if name == "submissions.jsonl":
            for record in parse_records("\n".join(new)):
                if isinstance(record.get("id"), str):
                    self.ever[record["id"]] = record
        if rows:
            self.store.append("events.jsonl", "".join(json.dumps(r) + "\n" for r in rows))

    def _gate(self, open_: bool) -> None:
        if self.cards is None or open_ == self.open:
            return
        try:
            os.chmod(self.cards, 0o755 if open_ else 0o000)
        except OSError:
            return
        self.open = open_
        self.store.append("events.jsonl", json.dumps(
            {"t": time.time(), "file": "cards", "event": "opened" if open_ else "closed"}) + "\n")

    def finish(self) -> dict:
        """A last look, every submission ever seen, and the cards left open for cleanup."""
        self.stopping.set()
        self.poll()
        with self.lock:
            raw = [line for line in self.lines["submissions.jsonl"] if line.strip()]
            final = {r.get("id") for r in parse_records("\n".join(raw))}
            lost = [r for sid, r in self.ever.items() if sid not in final]
            # The final lines exactly as written -- a malformed one is still reported
            # `invalid` -- then every line the agent removed, as last seen.
            self.store.write("submissions_all.jsonl", "".join(line + "\n" for line in raw)
                             + "".join(json.dumps(r) + "\n" for r in lost))
            if self.cards is not None:
                try:
                    os.chmod(self.cards, 0o755)
                except OSError:
                    pass
        return {"submissions_removed": sorted(r.get("id") for r in lost)}
