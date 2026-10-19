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

  * **Each step's output, as it stood when the step ended.** The agent says
    when it finishes a step -- `step.py done 2`, `step.py done 3` -- and the
    findings file at that moment is copied to `steps/step<N>.findings.jsonl`.
    That is the step's output, whatever is written or changed afterwards.

  * **Root-cause cards from step 3 on.** The cards' directory is locked until
    the agent says step 2 is done, and open from then on, all of them; which
    units it read is the agent's own choice. While locked, a note beside it
    says how to open it -- a bare "Permission denied" read as a permanent
    restriction, and the agent in the first gated run never tried again.

No permission stops an agent running as the same user from editing its own
files or from `chmod`; what this guarantees is that nothing it does is lost,
and the run's audit flags any `chmod`.
"""

from __future__ import annotations

import difflib
import json
import os
import sys
import threading
import time
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lib.progress import parse_records  # noqa: E402

FILES = ("findings.jsonl", "submissions.jsonl")
NOTE = "ROOT-CAUSE-CARDS-LOCKED.md"


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
        self.done: list[int] = []                     # steps the agent has said are finished
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

    def declare(self, step: int) -> dict:
        """The agent says `step` is finished: keep the findings as they are now."""
        self.poll()                                   # what it wrote just before saying so
        with self.lock:
            new = [n for n in range(2, step + 1) if n not in self.done]
            records = parse_records("\n".join(self.lines["findings.jsonl"]))
            for n in new:                             # `done 3` without `done 2` finishes both
                self.done.append(n)
                self.store.write(f"steps/step{n}.findings.jsonl",
                                 "".join(line + "\n" for line in self.lines["findings.jsonl"]))
                self.store.append("events.jsonl", json.dumps(
                    {"t": time.time(), "file": "steps", "event": "done", "step": n,
                     "records": sum(r.get("step") == n for r in records)}) + "\n")
            if 2 in self.done:
                self._gate(True)
        units = sorted({r.get("unit") for r in records if r.get("step") == step and r.get("unit")})
        cards = " All the root-cause cards are open now." if self.cards is not None and step == 2 else ""
        after = ("" if step == 2 else " Step 4 may begin: inputs.py and verify.py will run.")
        already = "" if new else " (it was already recorded as finished)"
        return {"done": list(self.done), "message":
                f"Step {step} is recorded as finished{already}: {len(units)} unit(s) have a "
                f"step-{step} record, kept as they are now.{cards}{after}"}

    def _gate(self, open_: bool) -> None:
        if self.cards is None:
            return
        if not open_:
            self._note()
        if open_ == self.open:
            return
        try:
            os.chmod(self.cards, 0o755 if open_ else 0o000)
        except OSError:
            return
        if open_:
            (self.cards.parent / NOTE).unlink(missing_ok=True)
        self.open = open_
        self.store.append("events.jsonl", json.dumps(
            {"t": time.time(), "file": "cards", "event": "opened" if open_ else "closed"}) + "\n")

    def _note(self) -> None:
        """Say, beside the locked directory, why it is locked and what opens it."""
        text = ("# The root-cause cards are locked until step 3\n\n"
                "This is by design, not a fault: step 2 is your own reading, made before any "
                "card. When you have finished step 2 -- its records written to `findings.jsonl` "
                "in the repository root -- say so:\n\n"
                "    python $SKILL/scripts/step.py done 2\n\n"
                "and every card in `root-causes/` opens, and stays open.\n")
        try:
            path = self.cards.parent / NOTE
            if not path.exists() or path.read_text() != text:
                path.write_text(text)
        except OSError:
            pass

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
                    (self.cards.parent / NOTE).unlink(missing_ok=True)
                except OSError:
                    pass
        return {"submissions_removed": sorted(r.get("id") for r in lost)}
