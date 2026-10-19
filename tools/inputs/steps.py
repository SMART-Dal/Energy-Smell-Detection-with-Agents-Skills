"""Keep each step's output as the agent leaves it, and open the root-cause cards at step 3.

The agent writes one file per step in the repository's root and says when the
step is finished:

    step 1   step1.jsonl                          python $SKILL/scripts/step.py done 1
    step 2   step2.jsonl                          python $SKILL/scripts/step.py done 2
    step 3   step3.jsonl                          python $SKILL/scripts/step.py done 3
    step 4   submissions.jsonl, step4.jsonl       python $SKILL/scripts/step.py done 4

Nothing is watched in between. While a step is open its file is the agent's to
write and rewrite as it likes. At `done N` the service copies that step's files
into our record (`steps/`), where the agent cannot reach, and makes the agent's
copies read-only: a finished step is never changed, and what we kept is that
step's output. Steps finish in order, one after the other.

Two more things, both event-driven:

  * the root-cause cards are locked until `done 2`, with a note beside them
    saying how they open -- a bare "Permission denied" read as permanent;
  * verify.py reports every repair it measures (`measured.jsonl`), so a repair
    the agent deletes during step 4 is still kept, and the review measures it
    (`submissions_all.jsonl`).

The agent runs as the same user and could undo a chmod; at every `done` and at
the end, the files of finished steps are compared with our copies, and any
change is logged (the run's audit also flags a chmod).
"""

from __future__ import annotations

import hashlib
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

FILES = {1: ["step1.jsonl"], 2: ["step2.jsonl"], 3: ["step3.jsonl"],
         4: ["step4.jsonl", "submissions.jsonl"]}
OPTIONAL = {"submissions.jsonl"}                       # a run may end with nothing to measure
NOTE = "ROOT-CAUSE-CARDS-LOCKED.md"
NEXT = {
    1: "Step 2: read each unit and write step2.jsonl, one record per unit.",
    2: "Step 3: decide every suspicion and write step3.jsonl.{cards}",
    3: "Step 4: ask for the inputs, write submissions.jsonl and step4.jsonl; inputs.py and "
       "verify.py will run now.",
    4: "All four steps are finished. End with your summary.",
}


def digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


class StepKeeper:
    def __init__(self, repo: Path, store, cards: Path | None):
        self.repo = Path(repo)
        self.store = store
        self.cards = Path(cards) if cards else None
        self.done: list[int] = []
        self.kept: dict[str, str] = {}                 # file -> digest when its step finished
        self.lock = threading.Lock()
        if self.cards is not None:
            self._cards(open_=False)

    def _event(self, **row) -> None:
        self.store.append("events.jsonl", json.dumps({"t": time.time(), **row}) + "\n")

    def _cards(self, open_: bool) -> None:
        note = self.cards.parent / NOTE
        try:
            os.chmod(self.cards, 0o755 if open_ else 0o000)
            if open_:
                note.unlink(missing_ok=True)
            else:
                note.write_text(
                    "# The root-cause cards are locked until step 3\n\n"
                    "This is by design, not a fault: step 2 is your own reading, made before any "
                    "card. When step 2 is finished, run\n\n"
                    "    python $SKILL/scripts/step.py done 2\n\n"
                    "and every card in `root-causes/` opens, and stays open.\n")
        except OSError:
            return
        self._event(file="cards", event="opened" if open_ else "closed")

    def _changed_since_kept(self) -> list[str]:
        """Files of finished steps that no longer match our copy."""
        changed = [name for name, kept in self.kept.items() if digest(self.repo / name) != kept]
        for name in changed:
            self._event(file=name, event="changed_after_done")
        return changed

    def declare(self, step: int) -> dict:
        with self.lock:
            if step in self.done:
                return {"ok": True, "done": list(self.done),
                        "message": f"Step {step} was already finished. {NEXT[step].format(cards='')}"}
            expected = len(self.done) + 1
            if step != expected:
                return {"ok": False, "error": f"step {expected} is not finished yet: finish it and run "
                        f"`python $SKILL/scripts/step.py done {expected}` first"}
            names = FILES[step]
            missing = [n for n in names if n not in OPTIONAL and not (self.repo / n).is_file()]
            if missing:
                return {"ok": False, "error": f"{', '.join(missing)} is not in the repository root; "
                        f"write step {step}'s records there, then run this again"}
            records = parse_records((self.repo / names[0]).read_text(errors="replace"))
            if not records:
                return {"ok": False, "error": f"{names[0]} has no record in it yet"}
            self._changed_since_kept()
            early = [n for later in range(step + 1, 5) for n in FILES[later]
                     if n not in OPTIONAL and (self.repo / n).exists()]
            for name in early:
                self._event(file=name, event="written_early", during_step=step)
            for name in names:
                path = self.repo / name
                if not path.is_file():
                    continue
                self.store.write(f"steps/{name}", path.read_text(errors="replace"))
                self.kept[name] = digest(path)
                try:
                    os.chmod(path, 0o444)
                except OSError:
                    pass
            self.done.append(step)
            self._event(file="steps", event="done", step=step, records=len(records))
            if step == 2 and self.cards is not None:
                self._cards(open_=True)
        cards = " All the root-cause cards are open now." if self.cards is not None else ""
        return {"ok": True, "done": list(self.done), "message":
                f"Step {step} is finished: {', '.join(n for n in names if n in self.kept)} "
                f"({len(records)} record(s)) kept as it is now, and read-only from here on. "
                + NEXT[step].format(cards=cards)}

    def measured(self, record) -> dict:
        if isinstance(record, dict):
            with self.lock:
                self.store.append("measured.jsonl", json.dumps({"t": time.time(), "record": record}) + "\n")
        return {"ok": True}

    def finish(self) -> dict:
        """Keep what an unfinished step left, check the finished ones, and list every repair."""
        with self.lock:
            self._changed_since_kept()
            unfinished = []
            for step, names in FILES.items():
                if step in self.done:
                    continue
                for name in names:
                    if (self.repo / name).is_file():
                        self.store.write(f"steps/unfinished/{name}",
                                         (self.repo / name).read_text(errors="replace"))
                        unfinished.append(name)
            final_path = self.repo / "submissions.jsonl"
            raw = [l for l in (final_path.read_text(errors="replace").splitlines()
                               if final_path.is_file() else []) if l.strip()]
            final_ids = {r.get("id") for r in parse_records("\n".join(raw))}
            last: dict[str, dict] = {}
            for row in parse_records(self.store.read("measured.jsonl") or ""):
                record = row.get("record") or {}
                if isinstance(record.get("id"), str):
                    last[record["id"]] = record
            lost = [r for sid, r in last.items() if sid not in final_ids]
            # The final file exactly as written -- a malformed line is still reported
            # `invalid` -- then every measured repair the agent removed, as measured.
            self.store.write("submissions_all.jsonl", "".join(l + "\n" for l in raw)
                             + "".join(json.dumps(r) + "\n" for r in lost))
            if self.cards is not None:
                self._cards(open_=True)
        return {"steps_done": list(self.done), "unfinished_files": unfinished,
                "submissions_removed": sorted(r.get("id") for r in lost)}
