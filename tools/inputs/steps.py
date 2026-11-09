"""Keep each step's output as the agent leaves it, and open the root-cause cards at step 2.

The agent writes one file per step in the repository's root and says when the
step is finished:

    step 1   step1.jsonl                          python $SKILL/scripts/step.py done 1
    step 2   step2.jsonl                          python $SKILL/scripts/step.py done 2
    step 3   submissions.jsonl, step3.jsonl       python $SKILL/scripts/step.py done 3

Nothing is watched in between. While a step is open its file is the agent's to
write and rewrite as it likes. At `done N` the service copies that step's files
into our record (`steps/`), where the agent cannot reach, and makes the agent's
copies read-only: a finished step is never changed, and what we kept is that
step's output. Steps finish in order, one after the other.

Three more things, all event-driven:

  * the root-cause cards are locked until `done 1`, with a note beside them
    saying how they open -- a bare "Permission denied" read as permanent.
    Step 1 finds with the one-line index; the cards are for deciding;
  * in an arm with rules, scan.py reports each comparison of the rules with
    step1.jsonl (`scans.jsonl`), and `done 1` refuses until one was made. That
    it ran is all that is checked: what the agent makes of the file is its own
    judgement;
  * verify.py reports every repair it measures (`measured.jsonl`), so a repair
    the agent deletes during step 3 is still kept, and the review measures it
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

from lib.progress import VERDICTS, parse_records  # noqa: E402

FILES = {1: ["step1.jsonl"], 2: ["step2.jsonl"], 3: ["step3.jsonl", "submissions.jsonl"]}
LAST = max(FILES)
CARDS_OPEN_AT = 1                                      # done 1: step 2 decides with the cards
OPTIONAL = {"submissions.jsonl"}                       # a run may end with nothing to measure
NOTE = "ROOT-CAUSE-CARDS-LOCKED.md"
NEXT = {
    1: "Step 2: read each unit on your list and decide every suspicion, and write step2.jsonl, "
       "one record per unit.{cards}",
    # Inputs open at step 3, not 2: asked for in step 2, they were asked for
    # before any card was read, and the decisions written after them followed.
    2: "Step 3: write submissions.jsonl and step3.jsonl; inputs.py and verify.py run now.",
    3: "All three steps are finished. End with your summary.",
}


def _open_cards(records: list) -> str:
    """The cards step 2 needs, named from the agent's own step 1.

    "The cards are open now" was not enough: an agent that had met the lock in
    step 1 wrote every decision without opening one.
    """
    named = sorted({str(s.get("root_cause")) for r in records if isinstance(r, dict)
                    for s in r.get("suspicions") or [] if isinstance(s, dict) and s.get("root_cause")},
                   key=lambda rc: [int(p) if p.isdigit() else 0 for p in rc.replace("C", "").split(".S")])
    opened = " All the root-cause cards are open now, and stay open."
    if not named:
        return opened
    return (opened + " Read the card of every root cause you suspected before deciding it: "
            + ", ".join(f"$SKILL/reference/root-causes/{rc}.md" for rc in named) + ".")


def digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


class StepKeeper:
    def __init__(self, repo: Path, store, cards: Path | None, scanner: bool = False):
        self.repo = Path(repo)
        self.store = store
        self.cards = Path(cards) if cards else None
        self.scanner = scanner                         # the arm ships scan.py
        self.scans: list[dict] = []                    # each comparison, as scan.py sent it
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
                    "# The root-cause cards are locked until step 2\n\n"
                    "This is by design, not a fault: step 1 finds, with the one-line index in "
                    "`reference/README.md`; the cards are for deciding, in step 2. When step 1 "
                    "is finished, run\n\n"
                    "    python $SKILL/scripts/step.py done 1\n\n"
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

    def scanned(self, request: dict) -> dict:
        """Keep one comparison of the rules with step1.jsonl, as scan.py sent it."""
        row = {k: v for k, v in request.items() if k != "op"}
        with self.lock:
            self.scans.append(row)
            self.store.append("scans.jsonl", json.dumps({"t": time.time(), **row}) + "\n")
        return {"ok": True}

    def _scan_refusal(self) -> str | None:
        """Why step 1 cannot finish yet in an arm with rules: they were never
        compared with the list. Only that the comparison ran is checked; what the
        agent makes of it, and what it lists afterwards, is its own judgement."""
        if self.scans:
            return None
        return ("before step 1 is finished, compare the rules with your list: run "
                "`python $SKILL/scripts/scan.py .` from the repository's root. It reads "
                "step1.jsonl and writes what it finds to one file; read it, add what you "
                "agree with, then run this again.")

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
            refusal = self._scan_refusal() if step == 1 and self.scanner else None
            if refusal:
                self._event(file="steps", event="refused", step=step, why="no comparison")
                return {"ok": False, "error": refusal}
            self._changed_since_kept()
            early = [n for later in range(step + 1, LAST + 1) for n in FILES[later]
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
            if step == CARDS_OPEN_AT and self.cards is not None:
                self._cards(open_=True)
        cards = _open_cards(records) if step == CARDS_OPEN_AT and self.cards is not None else ""
        return {"ok": True, "done": list(self.done), "message":
                f"Step {step} is finished: {', '.join(n for n in names if n in self.kept)} "
                f"({len(records)} record(s)) kept as it is now, and read-only from here on. "
                + NEXT[step].format(cards=cards)}

    def measured(self, record) -> dict:
        if isinstance(record, dict):
            with self.lock:
                self.store.append("measured.jsonl", json.dumps({"t": time.time(), "record": record}) + "\n")
        return {"ok": True}

    def on_record(self) -> dict:
        """Each repair's measurement as verify.py sent it, by id -- deleted lines
        included. A verdict, once there, is the one kept: it is what holds the
        repair's place, and what verify.py restores if the line loses it."""
        with self.lock:
            rows = parse_records(self.store.read("measured.jsonl") or "")
        kept: dict[str, dict] = {}
        for row in rows:
            record = row.get("record") or {}
            sid, measurement = record.get("id"), record.get("agent_measurement")
            if not isinstance(sid, str) or not isinstance(measurement, dict):
                continue
            if (kept.get(sid) or {}).get("status") not in VERDICTS:
                kept[sid] = measurement
        return {"ok": True, "measured": kept}

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
