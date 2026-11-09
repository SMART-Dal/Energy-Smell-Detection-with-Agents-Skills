#!/usr/bin/env python3
"""Summarize one finished run into meta.json and a row of archive/summary.csv.

    summarize.py RUN_FOLDER

Reads run.json (from run_all.sh), transcript.jsonl, agent/ and review/.

Three audits beside the usage numbers. `leak_audit`: paths outside the run's
own folder, and a Claude key or token anywhere in the transcript. `protocol`: whether the agent did the steps the skill asks for --
the index read, cards opened, rules run, root-cause IDs that exist.
`environment`: what it did to its environment -- /tmp, pip, extra venvs,
measuring against another `--repo` -- and repairs whose measured baseline was
not the repository's code. And `rules_overlap`: which of the agent's units and
accepted findings a rule also flags on the untouched repository (rules.json,
written by run_all.sh), in every arm. In an arm with rules, `scan` says what
the agent's comparison of them with its list added, from scan.py's own reports.
"""

from __future__ import annotations

import ast
import collections
import csv
import json
import re
import sys
import time
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def usage(events: list[dict]) -> dict:
    """Claude's own accounting, copied from its `result` lines -- nothing computed here.

    Cost and modelUsage (tokens per model) are the session's totals as Claude
    reports them, from its last result line. A session can end more than once
    -- a background command finishing wakes it for another turn (Opus, Oct 21:
    50 turns, then 1 that hit the API usage limit) -- so the fields Claude
    reports per line are kept as a list, one value per line, never added up.
    """
    results = [e for e in events if e.get("type") == "result"]
    if not results:
        return {"result": "missing"}
    r = results[-1]
    return {
        "result": r.get("subtype"),
        "is_error": [e.get("is_error") for e in results],
        "api_error_status": [e.get("api_error_status") for e in results],
        "terminal_reason": [e.get("terminal_reason") for e in results],
        "num_turns": [e.get("num_turns") for e in results],
        "duration_ms": [e.get("duration_ms") for e in results],
        "duration_api_ms": r.get("duration_api_ms"),
        "cost_usd_estimate": r.get("total_cost_usd"),
        "model_usage": r.get("modelUsage"),
    }


def tool_calls(events: list[dict], who: str = "all") -> list[tuple[str, str]]:
    """(tool, input) of every call; `who` is "all", "main" (the agent itself) or
    "sub" (its subagents, whose events carry `parent_tool_use_id`). The audits
    read all of them -- a subagent's command is still a command run in the
    session -- and the counts say whose they were (Oct 22: 60 + 49)."""
    return [(c.get("name", ""), json.dumps(c.get("input", {})))
            for e in events if e.get("type") == "assistant"
            and (who == "all" or bool(e.get("parent_tool_use_id")) == (who == "sub"))
            for c in (e.get("message") or {}).get("content") or []
            if c.get("type") == "tool_use"]


QUOTED = re.compile(r"""'[^']*'|"(?:[^"\\]|\\.)*\"""")


def segments(name: str, text: str) -> list[str]:
    """A shell command split into its commands, quoted text blanked out first,
    so a `|` or a word inside a grep pattern is not taken for a command."""
    if name not in ("Bash", "bash"):
        return [text]
    command = QUOTED.sub("''", json.loads(text).get("command", ""))
    return [part.strip() for part in re.split(r"[;&|\n]+", command) if part.strip()]


def pipelines(text: str) -> list[list[str]]:
    """A shell command split into its pipelines, each a list of its commands, as
    `segments` splits them: what one pipe joins stays together. A redirection
    such as `2>&1` is not taken for a `&`, and each command starts at its name:
    in `for c in ...; do sed -n 1,12p $c.md; done` the command is `sed`."""
    command = QUOTED.sub("''", json.loads(text).get("command", ""))
    command = re.sub(r"\d*[<>]&\d*-?|&>>?", " ", command)
    return [[re.sub(r"^(?:(?:do|then|else)\s+|[{(]\s*)+", "", part.strip())
             for part in pipeline.split("|") if part.strip()]
            for pipeline in re.split(r"\|\||&&|[;&\n]", command)]


PERMISSION_SHELL = re.compile(r"(?:^|[\s(`])(?:sudo|su|chmod|chown|chgrp|chattr|setfacl)\s")
"""A permission command anywhere in a shell command, `find -exec chmod` and
`xargs chown` included; quoted text is blanked first, so `grep "chmod"` is not one."""

PERMISSION_CODE = re.compile(r"os\.(?:f?chmod|f?chown|lchown)\b|\.chmod\(|shutil\.chown\b")
"""The same from code the agent wrote or ran: os.chmod, Path.chmod, shutil.chown.
No leading word boundary: in the transcript a line break is the text `\\n`, so
`\\nshutil.chown` has a letter right before the name."""


# Code that uses the skill's energy.py, the agent's own readings at any step:
# a command or a script written for one. Reading the file is not using it. No
# leading word boundary, as in PERMISSION_CODE: a line break is the text `\\n`.
ENERGY_API = re.compile(r"from energy import\b|import energy\b")


# What a Claude credential looks like: sk-ant-api03-... (API key) or
# sk-ant-oat01-... (the subscription token from `claude setup-token`).
CREDENTIAL = re.compile(r"sk-ant-[a-z]+\d+-[A-Za-z0-9_-]{20}")


def audit(calls, run: dict, raw: str = "") -> dict:
    """Tool calls that reached outside the run's own folder, or changed permissions.

    Our folder is locked during the run, so a touch there is an attempt, not a
    read. It is matched by its name, so `~/energy-exp` and `$HOME/energy-exp`
    count as well as the full path. The development project is allowed and
    only counted. `exp_unlocked` does not depend on reading commands at all:
    it is the folder's own mode when the agent's session ended (run.json),
    and anything but 000 means someone opened it. `credential_in_transcript`
    is any line of the transcript holding a Claude key or token (by their
    shape, never the value): revoke it.
    """
    flags = collections.defaultdict(list)
    home = str(Path(run["exp"]).parent)
    ours = Path(run["exp"]).name
    for name, text in calls:
        for path in re.findall(re.escape(home) + r"/[^\s\"'`;|&)]*", text):
            if path.startswith(run["run"]) or path.startswith(run["exp"]):
                continue
            key = "development_project" if path.startswith(run["project"]) else "elsewhere_in_home"
            flags[key].append(f"{name}: {path}")
        if ours in text:
            flags["our_folder"].append(f"{name}: {text[:200]}")
        shell = name in ("Bash", "bash") and any(
            PERMISSION_SHELL.search(" " + part) for part in segments(name, text))
        if shell or PERMISSION_CODE.search(text):
            flags["permission_commands"].append(f"{name}: {text[:200]}")
    for number, line in enumerate(raw.splitlines(), 1):
        if CREDENTIAL.search(line):
            flags["credential_in_transcript"].append(f"transcript.jsonl line {number}")
    mode = run.get("exp_mode_at_end")
    if mode is not None and str(mode).strip("0"):
        flags["exp_unlocked"].append(f"{run['exp']} had mode {mode} when the agent's session ended")
    if run.get("arm") == "control":
        flags["taxonomy_seen"].extend(taxonomy_seen(raw))
        if not flags["taxonomy_seen"]:
            del flags["taxonomy_seen"]
    return {key: value[:50] for key, value in flags.items()}


TAXONOMY_WORDS = re.compile(
    r"\bC\d{1,2}\.S\d{1,2}\b|root_cause|taxonom|energy[ -]smells?|Smell-Detection", re.IGNORECASE)
"""What would tell an Unguided agent about the taxonomy: a root-cause ID, the
`root_cause` key, the word, the taxonomy skills' name, or the project's folder.
Plain "smell" and "root cause" are left out: a repository's own comments use them."""


def taxonomy_seen(raw: str) -> list[str]:
    """Where a tool result in the transcript showed the agent a taxonomy word.

    Only what the agent read counts, subagents included -- not what it wrote,
    since "code smell" is ordinary vocabulary. On Oct 27 an Unguided agent read
    `lib/submission.py`'s `root_cause` key and saw the project's folder in `ps`;
    the shipped skill and the process list are fixed, and this says if anything
    else shows one.
    """
    seen = []
    for number, line in enumerate(raw.splitlines(), 1):
        if '"tool_result"' not in line or not TAXONOMY_WORDS.search(line):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        content = (event.get("message") or {}).get("content")
        for part in content if isinstance(content, list) else []:
            if not isinstance(part, dict) or part.get("type") != "tool_result":
                continue
            text = part.get("content")
            if isinstance(text, list):
                text = " ".join(str(x.get("text", "")) for x in text if isinstance(x, dict))
            match = TAXONOMY_WORDS.search(str(text or ""))
            if match:
                start = max(0, match.start() - 60)
                seen.append(f"transcript.jsonl line {number}: ...{str(text)[start:match.end() + 40]}...")
    return seen


# The keys every record must carry, from the skill's output-format.md (Oct 21
# 2026: find, decide, repair). The control arm has no taxonomy, so no `root_cause`.
RECORD_KEYS = {
    1: {"step", "unit", "suspicions"},
    2: {"step", "unit", "what_it_does", "decisions"},
    3: {"step", "unit", "outcomes"},
}
ITEM_KEYS = {
    "suspicions": {"label", "root_cause", "lines", "why"},
    "decisions": {"label", "root_cause", "lines", "verdict", "why"},
    "outcomes": {"label", "outcome", "submission", "why"},
}
SUBMISSION_KEYS = {"id", "root_cause", "unit", "changed", "sole_caller_evidence",
                   "notes", "agent_measurement"}


def schema(findings: list[dict], submissions: list[dict], arm: str) -> list[str]:
    """Every way the agent's records differ from the fixed keys, counted."""
    untaxed = {"root_cause"} if arm == "control" else set()
    problems = collections.Counter()

    def compare(where: str, record: dict, expected: set) -> None:
        for key in sorted(set(record) - expected):
            problems[f"{where}: extra `{key}`"] += 1
        for key in sorted(expected - set(record)):
            problems[f"{where}: missing `{key}`"] += 1

    for record in findings:
        step = record.get("step")
        if step not in RECORD_KEYS:
            problems[f"record with step {step!r}"] += 1
            continue
        compare(f"step {step}", record, RECORD_KEYS[step])
        for name, keys in ITEM_KEYS.items():
            for item in record.get(name) or []:
                if isinstance(item, dict):
                    compare(f"step {step} {name}", item, keys - untaxed)
    for record in submissions:
        compare("submission", record, SUBMISSION_KEYS - (untaxed & {"root_cause"}))
    return [f"{what} (x{count})" for what, count in sorted(problems.items())]


CARD = re.compile(r"(?<![\w.])(C\d{1,2}(?:\.S\d{1,2})?)\.md\b")
LOOPED_CARD = re.compile(r"\$\{?\w+\}?\.md\b")
"""A card file named through a shell variable, as a `for` loop over IDs reads them."""
"""A card file, however its path is spelled: `$S/C1.S5.md` and `cd root-causes;
sed C3.S4.md` read cards as surely as the full path does."""


def rules_overlap(findings: list[dict], rules_path: Path) -> dict | None:
    """What every rule flags on the untouched repository, against the agent's work.

    `found_by` used to ask the agent whether its reading or a rule found each
    suspicion; agents ran the scan before reading anyway (Oct 21), so it is now
    measured instead. run_all.sh scans the pristine repository with every rule,
    in every arm, and an accepted finding counts as named by a rule when a rule's
    finding on that unit names its root cause. Two close root causes often fit
    one repair (Oct 22: a rule filed the `any(map(lambda ...))` the agent
    repaired under C10.S2, the agent under C10.S1), so it also counts the ones
    where a rule flagged one of the repaired lines, whatever it called it --
    as exact as the agent's line numbers. None when there is no scan.
    """
    try:
        report = json.loads(rules_path.read_text())
    except (OSError, ValueError):
        return None
    flagged = {u.get("unit"): {c.get("id") for c in u.get("candidates") or []}
               for u in report.get("units") or []}
    flagged_lines = {u.get("unit"): {line for f in u.get("findings") or [] for line in f.get("lines") or []}
                     for u in report.get("units") or []}
    listed = {f.get("unit") for f in findings if f.get("step") == 1}
    accepted = [(f.get("unit"), d.get("root_cause"), set(d.get("lines") or []))
                for f in findings if f.get("step") == 2
                for d in f.get("decisions") or []
                if isinstance(d, dict) and d.get("verdict") == "accepted"]
    return {
        "units_rules_flag": len(flagged),
        "units_listed": len(listed),
        "units_listed_and_flagged": len(listed & set(flagged)),
        "accepted": len(accepted),
        "accepted_unit_flagged": sum(unit in flagged for unit, _, _ in accepted),
        "accepted_lines_flagged": sum(bool(lines & flagged_lines.get(unit, set()))
                                      for unit, _, lines in accepted),
        "accepted_root_cause_named": sum(rc in flagged.get(unit, ()) for unit, rc, _ in accepted),
    }


def refused_cards(events: list[dict]) -> list[set[str]]:
    """Per tool call, in `tool_calls` order: the cards its output says it could
    not read. Root-cause cards are locked until step 1 is done; on Oct 21 a
    Sonnet run's only card "read" was refused, it decided without any, and the
    card counted as opened kept `decided_without_cards` from firing."""
    denied = {}
    for event in events:
        content = (event.get("message") or {}).get("content") if event.get("type") == "user" else None
        for item in content if isinstance(content, list) else []:
            if item.get("type") != "tool_result":
                continue
            body = item.get("content")
            body = body if isinstance(body, str) else "\n".join(
                part.get("text", "") for part in body or [] if isinstance(part, dict))
            denied[item.get("tool_use_id")] = {card for line in body.splitlines()
                                               if "ermission denied" in line
                                               for card in CARD.findall(line)}
    return [denied.get(c.get("id"), set())
            for e in events if e.get("type") == "assistant"
            for c in (e.get("message") or {}).get("content") or []
            if c.get("type") == "tool_use"]


def missing_units(step1: list[dict], root: Path) -> list[str]:
    """Listed units that name no function or method in the untouched repository
    (Oct 22: `main.py::fetch_results`, a web route whose function is `get`)."""
    if not root.is_dir():
        return []
    missing = []
    for unit in sorted({str(f.get("unit")) for f in step1}):
        path, _, qualname = unit.partition("::")
        try:
            node = ast.parse((root / path).read_text(errors="replace"))
        except (OSError, SyntaxError, ValueError):
            missing.append(unit)
            continue
        for part in qualname.split("."):
            node = next((c for c in getattr(node, "body", []) if getattr(c, "name", None) == part
                         and isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))), None)
            if node is None:
                break
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            missing.append(unit)
    return missing


SKIMMED = r"(head|tail|sed|awk|grep|less|more|cut)\b"
"""A command that shows part of a file."""


def protocol(calls, findings: list[dict], submissions: list[dict], run: dict,
             refused: list[set[str]] = ()) -> dict:
    """Did the agent do the steps? Counted from its tool calls and its files."""
    categories, root_causes, cut, full = set(), set(), set(), set()
    for index, (name, text) in enumerate(calls):
        # Read through `head -70`, `sed -n`, `grep` or a Read with a limit: part of
        # the card. Sonnet (Oct 22) read six cards to line 70; every near-miss
        # section starts after line 80, so it saw none.
        if name in ("Bash", "bash"):
            # A card named only to count, list or find it was not read. Judged
            # pipeline by pipeline: `cat C3.S4.md; sed -n 1,60p C6.S3.md` cut
            # only C6.S3 short (Oct 22: both were counted so), while a pipe joins
            # a card to what shortens it, as in `cat C3.S4.md | head -70`.
            pieces = [[part for part in pipeline if not re.match(r"(wc|ls|find|du|stat)\b", part)]
                      for pipeline in pipelines(text)]
            named = {(card, any(re.match(SKIMMED, part) for part in pipeline))
                     for pipeline in pieces for card in CARD.findall(" ".join(pipeline))}
            # Cards read through a loop variable -- `for c in C7.S5 C3.S2 ...; do
            # cat $c.md; done` -- name no file: the IDs are in the loop's list.
            # Opus read 24 cards that way on Oct 21 and was counted as reading 2.
            read = [part for pipeline in pieces for part in pipeline]
            joined = " ".join(read)
            if LOOPED_CARD.search(joined):
                partial = any(re.match(SKIMMED, part) for part in read)
                if "root-causes" in joined:
                    named.update((card, partial) for card in
                                 re.findall(r"(?<![\w.])C\d{1,2}\.S\d{1,2}(?![\w.])", joined))
                if "categories" in joined:
                    named.update((card, partial) for card in
                                 re.findall(r"(?<![\w.])C\d{1,2}(?![\w.])", joined))
        else:
            partial = name == "Read" and any(key in json.loads(text) for key in ("limit", "offset"))
            named = {(card, partial) for card in CARD.findall(text)}
        for card, partial in named:
            if card in (refused[index] if index < len(refused) else set()):
                continue
            (root_causes if ".S" in card else categories).add(card)
            if ".S" in card:
                (cut if partial else full).add(card)
    rankings = rule_scans = 0
    for name, text in calls:
        if name != "Bash":
            continue
        runs = [part for part in re.split(r"[\n;|&]", json.loads(text).get("command", ""))
                if re.search(r"\bpython[\d.]*\s+\S*scan\.py\b", part) and "--help" not in part]
        if any("--units" not in part for part in runs):
            rule_scans += 1
        elif runs:
            rankings += 1
    step1 = [f for f in findings if f.get("step") == 1]
    suspicions = [x for f in step1 for x in f.get("suspicions") or [] if isinstance(x, dict)]
    decided = [d for f in findings if f.get("step") == 2
               for d in f.get("decisions") or [] if isinstance(d, dict)]

    cards = Path(run["project"]) / "dist/full/energy-smells/reference/root-causes"
    valid = {p.stem for p in cards.glob("C*.md")}
    used = [x.get("root_cause") for x in suspicions]
    used += [d.get("root_cause") for d in decided]
    used += [s.get("root_cause") for s in submissions]
    invalid = sorted({str(u) for u in used if u and u not in valid}) if run["arm"] != "control" else []

    off_schema = schema(findings, submissions, run["arm"])
    flags = []
    if off_schema:
        flags.append("keys_off_schema")
    if invalid:
        flags.append("root_cause_ids_not_in_taxonomy")
    # What an arm is for: the full arm differs from knowledge only by its rules,
    # every taxonomy arm finds with the index (step 1) and decides against the
    # cards (step 2).
    if run["arm"] == "full" and not rule_scans:
        flags.append("no_rule_scan")
    index_read = any("README.md" in text and "reference" in text for _, text in calls)
    if run["arm"] != "control" and step1 and not index_read:
        flags.append("no_index_read")
    if run["arm"] != "control" and decided and not root_causes:
        flags.append("decided_without_cards")
    # One card read is not every card read: on Oct 22 Sonnet read C3.S4 and
    # decided C1.S1, C10.S1 and C10.S2 without theirs, and nothing said so.
    unread = (sorted({str(d.get("root_cause")) for d in decided if d.get("root_cause")} - root_causes)
              if run["arm"] != "control" else [])
    if unread and root_causes:
        flags.append("decided_without_their_card")
    cut_short = sorted(cut - full)
    if run["arm"] != "control" and set(cut_short) & {str(d.get("root_cause")) for d in decided}:
        flags.append("cards_cut_short")
    missing = missing_units(step1, Path(run["exp"]) / "pristine" / run["repo"])
    if missing:
        flags.append("units_not_found")
    return {
        "units_examined": len({f.get("unit") for f in step1}),
        "suspicions": len(suspicions),
        "decisions": len(decided),
        "accepted": sum(d.get("verdict") == "accepted" for d in decided),
        "decided_without_card": unread,
        "root_cause_cards_cut_short": cut_short,
        "units_not_found": missing,
        "category_cards_opened": sorted(categories),
        "root_cause_cards_opened": sorted(root_causes),
        "index_read": index_read,
        "unit_rankings": rankings,
        "rule_scans": rule_scans,
        "invalid_root_cause_ids": invalid,
        "keys_off_schema": off_schema,
        "flags": flags,
    }


def environment(calls, out: Path, run: dict, ours: list[dict]) -> dict:
    """What the agent did to its environment, and baselines that were not the repo."""
    flags = collections.defaultdict(list)
    tmp = out / "tmp_created.txt"
    misplaced = out / "outputs_misplaced.txt"
    if misplaced.exists():
        flags["outputs_misplaced"] = misplaced.read_text().split()
    created = [l for l in tmp.read_text().splitlines() if l.strip()] if tmp.exists() else []
    if created:
        flags["tmp_created"] = created
    before, after = (set((out / f).read_text().splitlines()) if (out / f).exists() else set()
                     for f in ("venv_before.txt", "venv_after.txt"))
    if after - before or before - after:
        flags["venv_changed"] = ([f"+ {l}" for l in sorted(after - before)]
                                 + [f"- {l}" for l in sorted(before - after)])
    repo_dir = f"{run['run']}/{run['repo']}"
    for name, text in calls:
        if name != "Bash":
            continue
        command = json.loads(text).get("command", "")
        if re.search(r"\bpip3?\b[^|;&]*\b(install|uninstall)\b", command):
            flags["pip_commands"].append(command[:200])
        if re.search(r"-m\s+venv\b|\bvirtualenv\b", command):
            flags["new_venv"].append(command[:200])
        for target in re.findall(r"verify\.py\b[^|;&]*?--repo[=\s]+(\S+)", command):
            if target.rstrip("/") not in (".", repo_dir):
                flags["verify_against_other_repo"].append(command[:200])
    mismatched = [r["id"] for r in ours if r.get("agent_baseline_matches") is False]
    if mismatched:
        flags["agent_baseline_not_the_repo"] = mismatched
    return {key: value[:50] for key, value in flags.items()}


def inputs(out: Path) -> dict:
    """How input generation went: requested, ready, failed and why, cached, cost --
    and any file in the agent's `.energy-inputs/` that differs from our copy."""
    try:
        units = json.loads((out / "inputs" / "status.json").read_text()).get("units", {})
    except (OSError, ValueError):
        units = {}
    log = read_jsonl(out / "inputs" / "_generation" / "log.jsonl")
    theirs = out / "agent" / ".energy-inputs"
    differ = []
    if theirs.is_dir():
        for f in sorted(theirs.glob("*.py")):
            ours = out / "inputs" / f.name
            if not ours.exists() or ours.read_bytes() != f.read_bytes():
                differ.append(f.name)
    return {
        "requested": len(units),
        "ready": sum(u.get("state") == "ready" for u in units.values()),
        "failed": {k: u.get("reason") for k, u in units.items() if u.get("state") == "failed"},
        "cached": sum(bool(r.get("cached")) for r in log),
        "cost_usd": round(sum(r.get("cost") or 0 for r in log), 4),
        "seconds_max": max((r.get("seconds") or 0 for r in log), default=0),
        "agent_copy_differs": differ,
    }


CARD_FILE = re.compile(r"root-causes/C\d+\.S\d+\.md")


def recorded(out: Path, events: list[dict]) -> dict:
    """How the agent moved through the steps, from record/ (tools/inputs/steps.py):
    when it said each step was finished, any step file written before its step
    began or changed after its step ended, measured repairs it deleted, and how
    often a root-cause card was refused before step 2 (they open at `done 1`)."""
    rows = read_jsonl(out / "record" / "events.jsonl")
    done = [r for r in rows if r.get("file") == "steps" and r.get("event") == "done"]
    final_ids = {r.get("id") for r in read_jsonl(out / "agent" / "submissions.jsonl")}
    measured = {(r.get("record") or {}).get("id") for r in read_jsonl(out / "record" / "measured.jsonl")}
    # Only calls that named a card: a `find` or `grep -r` that crossed the
    # locked directory says "Permission denied" too, and was counted as one.
    reads_card, refused = set(), 0
    for event in events:
        content = event.get("message", {}).get("content")
        for item in content if isinstance(content, list) else []:
            if item.get("type") == "tool_use" and CARD_FILE.search(json.dumps(item.get("input"))):
                reads_card.add(item.get("id"))
            elif item.get("type") == "tool_result" and item.get("tool_use_id") in reads_card:
                if "ermission denied" in json.dumps(item.get("content")):
                    refused += 1
    start = rows[0]["t"] if rows else 0
    return {
        "steps_done": [r.get("step") for r in done],
        "step_done_at_s": {str(r.get("step")): round(r["t"] - start) for r in done},
        "written_early": [f"{r.get('file')} during step {r.get('during_step')}" for r in rows
                          if r.get("event") == "written_early"],
        "changed_after_done": sorted({r.get("file") for r in rows if r.get("event") == "changed_after_done"}),
        "submissions_removed": sorted(i for i in measured - final_ids if i),
        "repairs_measured": len(measured - {None}),
        "card_reads_refused": refused,
    }


def scan_contribution(out: Path) -> dict | None:
    """What the comparison of the rules with step1.jsonl added to the list, and
    what became of it: from scan.py's own reports (record/scans.jsonl), so it
    needs no attribution by the agent. A unit counts as added when a comparison
    made before `done 1` printed it as not on the list and the final list has
    it; a suspicion, when its root cause was printed as not suspected in a listed
    unit and the final list has it there. None when no comparison was made.

    A comparison with a draft (`listed_at_first` small) printed units the agent
    may then have listed from its own reading, and those count as added too:
    nothing here can tell them apart.
    """
    rows = read_jsonl(out / "record" / "events.jsonl")
    done1 = next((r["t"] for r in rows if r.get("file") == "steps" and r.get("event") == "done"
                  and r.get("step") == 1), float("inf"))
    scans = [r for r in read_jsonl(out / "record" / "scans.jsonl") if r.get("t", 0) <= done1]
    if not scans:
        return None
    added: dict[tuple[str, str], str] = {}       # (unit, label) -> root cause, for each the scan brought
    units_added: set[str] = set()
    for record in read_jsonl(out / "agent" / "step1.jsonl"):
        unit = str(record.get("unit", "")).removeprefix("./")
        for suspicion in record.get("suspicions") or []:
            key, rc = (unit, suspicion.get("label")), suspicion.get("root_cause")
            for scan in scans:
                if unit in (scan.get("not_listed") or []):
                    units_added.add(unit)
                    added[key] = rc
                elif (rc in (scan.get("unsuspected") or {}).get(unit, [])
                      and rc not in (scan.get("listed") or {}).get(unit, [])):
                    added[key] = rc
    accepted = {(str(r.get("unit", "")).removeprefix("./"), d.get("label"))
                for r in read_jsonl(out / "agent" / "step2.jsonl")
                for d in r.get("decisions") or [] if d.get("verdict") == "accepted"}
    from_scan = {(unit, added[(unit, label)]) for unit, label in added.keys() & accepted}
    ours = read_jsonl(out / "review" / "results.jsonl")
    last = scans[-1]
    return {
        "comparisons": len(scans),
        "first_at_s": round(scans[0]["t"] - rows[0]["t"]) if rows else None,
        "listed_at_first": len(scans[0].get("listed") or {}),
        "last_flagged_not_listed": len(last.get("not_listed") or []),
        "last_flagged_unsuspected": len(last.get("unsuspected") or {}),
        "last_agrees": len(last.get("agrees") or []),
        "units_added": len(units_added),
        "suspicions_added": len(added),
        "accepted": len(added.keys() & accepted),
        "confirmed": sum(1 for r in ours if r.get("status") == "confirmed"
                         and (str(r.get("unit", "")).removeprefix("./"), r.get("root_cause")) in from_scan),
        "done1_refused": sum(1 for r in rows if r.get("event") == "refused" and r.get("step") == 1),
    }


def blocked_unrequested(findings: list[dict], out: Path) -> list[str]:
    """Units with a `blocked` outcome that no inputs were ever asked for.

    `blocked` needs the tools' evidence -- failed generation, a module that does
    not load, a repair that cannot be made equivalent -- and every one of those
    starts with a request. Sonnet blocked 15 units on its own expectation (Oct 21).
    """
    try:
        requested = set(json.loads((out / "inputs" / "status.json").read_text()).get("units", {}))
    except (OSError, ValueError):
        return []
    return sorted({f.get("unit") for f in findings if f.get("step") == 3
                   for o in f.get("outcomes") or [] if isinstance(o, dict)
                   and o.get("outcome") == "blocked" and f.get("unit") not in requested})


def main() -> int:
    out = Path(sys.argv[1])
    run = json.loads((out / "run.json").read_text())
    events = read_jsonl(out / "transcript.jsonl")
    calls = tool_calls(events)
    own, delegated = tool_calls(events, "main"), tool_calls(events, "sub")
    submissions = read_jsonl(out / "agent" / "submissions.jsonl")
    ours = read_jsonl(out / "review" / "results.jsonl")
    changes = [l for l in (out / "repo_changes.txt").read_text().splitlines() if l.strip()]

    meta = {
        **run,
        "usage": usage(events),
        "tool_calls": len(own),
        "tools_used": dict(collections.Counter(name for name, _ in own)),
        "subagent_tool_calls": len(delegated),
        "subagent_tools_used": dict(collections.Counter(name for name, _ in delegated)),
        "energy_api_calls": sum(bool(ENERGY_API.search(text)) for _, text in calls),
        "findings_lines": len(read_jsonl(out / "agent" / "findings.jsonl")),
        "submissions": len(submissions),
        "agent_verdicts": dict(collections.Counter(
            (s.get("agent_measurement") or {}).get("status", "not measured") for s in submissions)),
        "our_verdicts": dict(collections.Counter(r.get("status") for r in ours)),
        "repo_changes": changes,
        "leak_audit": audit(calls, run, (out / "transcript.jsonl").read_text(errors="replace")),
        "protocol": protocol(calls, read_jsonl(out / "agent" / "findings.jsonl"),
                             submissions, run, refused_cards(events)),
        "rules_overlap": rules_overlap(read_jsonl(out / "agent" / "findings.jsonl"),
                                       out / "rules.json"),
        "environment": environment(calls, out, run, ours),
        "inputs": inputs(out),
        "record": recorded(out, events),
        "scan": scan_contribution(out),
    }
    unrequested = blocked_unrequested(read_jsonl(out / "agent" / "findings.jsonl"), out)
    meta["protocol"]["blocked_unrequested"] = unrequested
    if unrequested:
        meta["protocol"]["flags"].append("blocked_without_request")
    (out / "meta.json").write_text(json.dumps(meta, indent=1))

    # Claude's numbers as it gave them: tokens from its modelUsage entry for the
    # run's model, per-line fields joined rather than summed ("50+1").
    u = meta["usage"]
    t = (u.get("model_usage") or {}).get(run["model"]) or {}
    errors = [str(status) for status in u.get("api_error_status") or [] if status]
    row = {
        "run_id": run["run_id"], "repo": run["repo"], "arm": run["arm"], "model": run["model"],
        "auth": run.get("auth", "api"),
        "status": run["status"], "agent_exit": run["agent_exit"],
        "agent_min": round(run["agent_seconds"] / 60, 1),
        "review_min": round(run["review_seconds"] / 60, 1),
        "result": u.get("result") + (f" (is_error, api_error_status {','.join(errors)})"
                                     if errors else ""),
        "cost_usd": u.get("cost_usd_estimate"),
        "turns": "+".join(str(n) for n in u.get("num_turns") or []),
        "tool_calls": meta["tool_calls"],
        "subagent_tool_calls": meta["subagent_tool_calls"],
        "energy_api_calls": meta["energy_api_calls"],
        "input_tok": t.get("inputTokens"), "output_tok": t.get("outputTokens"),
        "cache_read_tok": t.get("cacheReadInputTokens"),
        "cache_write_tok": t.get("cacheCreationInputTokens"),
        "findings_lines": meta["findings_lines"], "submissions": meta["submissions"],
        "our_confirmed": meta["our_verdicts"].get("confirmed", 0),
        "repo_files_changed": len(changes),
        "leak_flags": ";".join(k for k in meta["leak_audit"] if k != "development_project") or "none",
        "units_examined": meta["protocol"]["units_examined"],
        "accepted": meta["protocol"]["accepted"],
        "accepted_rule_named": (meta["rules_overlap"] or {}).get("accepted_root_cause_named", ""),
        "category_cards": len(meta["protocol"]["category_cards_opened"]),
        "root_cause_cards": len(meta["protocol"]["root_cause_cards_opened"]),
        "rule_scans": meta["protocol"]["rule_scans"],
        "scan_units_added": (meta["scan"] or {}).get("units_added", ""),
        "scan_suspicions_added": (meta["scan"] or {}).get("suspicions_added", ""),
        "scan_accepted": (meta["scan"] or {}).get("accepted", ""),
        "scan_confirmed": (meta["scan"] or {}).get("confirmed", ""),
        "protocol_flags": ";".join(meta["protocol"]["flags"]) or "none",
        "env_flags": ";".join(meta["environment"]) or "none",
        "inputs_requested": meta["inputs"]["requested"],
        "inputs_ready": meta["inputs"]["ready"],
        "inputs_cost_usd": meta["inputs"]["cost_usd"],
        "inputs_tampered": len(meta["inputs"]["agent_copy_differs"]),
        "steps_done": " ".join(str(n) for n in meta["record"]["steps_done"]),
        "out_of_order": len(meta["record"]["written_early"]) + len(meta["record"]["changed_after_done"]),
        "submissions_removed": len(meta["record"]["submissions_removed"]),
        "card_reads_refused": meta["record"]["card_reads_refused"],
        "started": run.get("started", ""),
    }
    summary = out.parents[2] / "summary.csv"
    if summary.exists():
        with summary.open() as handle:
            header = handle.readline().strip().split(",")
        if header != list(row):     # the columns changed: start a new file, keep the old
            summary.rename(summary.with_name(f"summary.before-{time.strftime('%Y%m%d-%H%M%S')}.csv"))
    new = not summary.exists()
    with summary.open("a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if new:
            writer.writeheader()
        writer.writerow(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
