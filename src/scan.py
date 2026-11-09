#!/usr/bin/env python3
"""Static evidence for energy smells, compared with the list you wrote.

    python scan.py PATH                compare the rules with step1.jsonl, all of it into one file
    python scan.py PATH --json         every finding, machine-readable

The rules run after your own reading: until `step1.jsonl` exists in the
repository's root (this directory or one above it), the scan refuses. Then it
runs every rule over PATH and writes one file, `.energy-scan/<name>.txt`, in
three parts: units the rules flag that are not on your list; units on your list
where a rule names a root cause you did not suspect there; and units where a
rule agrees with you. Every entry carries its root causes, the fact, its lines
and the code on them. The terminal shows only how many entries each part holds:
one file, read whole, rather than a list on screen and the detail behind it in
a second place that the reader never opened.

It reports *facts* -- "a string is grown with += inside a loop at line 45" --
one entry per rule per unit, tagged with every root cause that fact could
indicate.  Within each part the units are in file and line order.  The order
says nothing about which ones matter; which code to read, and in what order, is
the reader's to decide.

Nothing here ever says a smell is present.  Whether a fact is a smell depends
on what the code is for and what the author was required to do, neither of
which an analyzer can see.  That judgement belongs to the reader.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.analysis.engine import (  # noqa: E402
    UnitFindings,
    analyse_path,
    available_analyzers,
    python_files,
)
from lib.signals import (  # noqa: E402
    Finding,
    SignalTable,
    group_findings,
    load_signals,
    rank_candidates,
)
from lib.inputs import SOCKET_ENV, ask  # noqa: E402
from lib.progress import parse_records  # noqa: E402

DETAIL_DIR = Path(".energy-scan")
"""Where the full report is written. Beside the caller's working directory
rather than beside the target, because the target is often somebody else's
repository and a scan should not leave anything in it."""

LIST = "step1.jsonl"
"""The agent's own list, which the rules are compared with. Until it exists the
scan refuses: in two runs the rules ran in the first minute,
before any file had been read, and one of them never compared them with the
list it later wrote, so nothing it listed came from them."""

LOCKED = (
    "The rules run after your own reading, so they are closed until step1.jsonl\n"
    "exists. Go through every file first, write what you found to step1.jsonl in\n"
    "the repository's root, then run this again: it compares the rules with your\n"
    "list and writes the result to one file.")

CODE_LINES = 6
"""Source lines shown under one message; the rest are counted, not printed."""


def _report_rule_errors() -> None:
    """Say on stderr which analyzers crashed, and how often.

    `rules.collect` catches an analyzer that raises so one brittle rule cannot
    abort a whole repo, which is right, and used to do it silently, which was
    not: a rule failing on a third of the units it saw looked exactly like a
    rule that found nothing there. Anyone computing precision over the scan
    would have been computing it over a rule that never ran.

    Imported here rather than at module scope because the `ruff` arm ships this
    file and withholds `lib/analysis/rules` -- a top-level import would turn a
    missing analyzer family into a crashing one.
    """
    try:
        from lib.analysis.rules import RULE_ERRORS
    except ImportError:
        return
    if not RULE_ERRORS:
        return
    total = sum(RULE_ERRORS.values())
    print(f"note: {total} analyzer failure(s) were caught and skipped; "
          f"findings from those units are incomplete", file=sys.stderr)
    for (rule, exception), count in sorted(RULE_ERRORS.items(),
                                           key=lambda kv: -kv[1]):
        print(f"  {rule} raised {exception} on {count} unit(s)", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="a .py file or a directory tree")
    parser.add_argument("--top", type=int, default=None,
                        help="how many findings to report (default: all)")
    parser.add_argument("--out", type=Path, default=DETAIL_DIR,
                        help=f"where to write the comparison (default {DETAIL_DIR}/)")
    parser.add_argument("--json", action="store_true",
                        help="emit every finding as JSON instead of the comparison")
    parser.add_argument(
        "--cross-unit", action="store_true",
        help="let rules see that a unit runs inside a caller's loop, across "
             "files; off by default, and dropping it returns the scan to "
             "file-at-a-time exactly")
    args = parser.parse_args(argv)

    if not args.path.exists():
        parser.error(f"no such path: {args.path}")

    # Outside a session, --json needs no list: it is every finding, for tooling.
    in_session = bool(os.environ.get(SOCKET_ENV))
    listing = _find_list(Path.cwd())
    if listing is None and (in_session or not args.json):
        print(LOCKED)
        return 2

    files = python_files(args.path)

    analyzers = available_analyzers()
    runnable = [name for name, blocked in analyzers.items() if blocked is None]
    if not runnable:
        # Each family explains its own absence, so this message stays the same
        # whatever families the installation happens to have.
        blockers = "\n  ".join(
            f"{name}: {why}" for name, why in analyzers.items()
        ) or "none are installed"
        if in_session and not args.json:
            # The comparison was attempted, so `done 1` must not wait for one
            # that can never be made.
            ask({"op": "scanned", "error": "no analyzer can run", "target": str(args.path)})
        parser.error(
            f"nothing can be analysed on this machine, so the scan would be "
            f"silently empty rather than clean:\n  {blockers}"
        )
    for name, why in analyzers.items():
        if why is not None:
            print(f"note: skipping {name} -- {why}", file=sys.stderr)

    findings = analyse_path(args.path, cross_unit=args.cross_unit, only_with_evidence=True)
    _report_rule_errors()
    table = load_signals()
    findings = [item for item in findings if item.evidence]
    grouped = [group_findings(item.evidence, table) for item in findings]
    ordered = _in_source_order(findings, grouped, args.path)
    shown = ordered[: args.top] if args.top else ordered

    if args.json:
        report = {
            "target": str(args.path),
            "files_scanned": len(files),
            "units_with_evidence": len(findings),
            "findings_total": len(ordered),
            "findings_shown": len(shown),
            "units": [_describe(findings[index], own, table, args.path)
                      for index, own in _by_unit(shown)],
        }
        json.dump(report, sys.stdout, indent=1)
        print()
        return 0

    # Named from the repository's root, as step1.jsonl names them, so the two
    # can be compared whatever directory was scanned.
    root = listing.parent
    units = [_describe(findings[index], own, table, root) for index, own in _by_unit(shown)]
    suspected = _suspected(listing)
    parts = _compare(units, suspected)
    path = _write_comparison(args, root, suspected, parts,
                             len(files), len(ordered), len(units))
    if in_session:
        ask({"op": "scanned", "target": str(args.path), "file": str(path),
             "listed": {unit: sorted(rcs) for unit, rcs in suspected.items()},
             "not_listed": [unit["unit"] for unit, _ in parts[0]],
             "unsuspected": {unit["unit"]: sorted({rc["id"] for f in shown_ for rc in f["root_causes"]})
                             for unit, shown_ in parts[1]},
             "agrees": [unit["unit"] for unit, _ in parts[2]]})
    print(_summary(listing, suspected, parts, path, len(files), len(units)))
    return 0


def _find_list(start: Path) -> Path | None:
    """step1.jsonl in the working directory or the nearest directory above it."""
    for directory in (start, *start.parents):
        if (directory / LIST).is_file():
            return directory / LIST
    return None


def _suspected(listing: Path) -> dict[str, set[str]]:
    """Each unit on the list, and the root causes suspected in it."""
    out: dict[str, set[str]] = {}
    for record in parse_records(listing.read_text(errors="replace")):
        unit = record.get("unit")
        if not isinstance(unit, str):
            continue
        rcs = out.setdefault(unit.removeprefix("./"), set())
        for suspicion in record.get("suspicions") or []:
            if isinstance(suspicion, dict) and isinstance(suspicion.get("root_cause"), str):
                rcs.add(suspicion["root_cause"])
    return out


def _compare(units: list[dict], suspected: dict[str, set[str]]) -> tuple[list, list, list]:
    """(not on the list, on it with a root cause not suspected there, agreeing),
    each as (unit, its findings that belong in that part).

    A fact sharing any root cause with the unit's suspicions agrees: two labels
    on one fact are one thing to look at, so the other label is not news.
    """
    missing, unsuspected, agrees = [], [], []
    for unit in units:
        mine = suspected.get(unit["unit"])
        if mine is None:
            missing.append((unit, unit["findings"]))
            continue
        new = [f for f in unit["findings"] if not {rc["id"] for rc in f["root_causes"]} & mine]
        same = [f for f in unit["findings"] if {rc["id"] for rc in f["root_causes"]} & mine]
        if new:
            unsuspected.append((unit, new))
        if same:
            agrees.append((unit, same))
    return missing, unsuspected, agrees


PART_TITLES = (
    "the rules flag {n} unit(s) that are not on your list",
    "{n} unit(s) on your list where a rule names a root cause you did not suspect there",
    "{n} unit(s) on your list where a rule agrees with you",
)


def _write_comparison(args, root: Path, suspected: dict, parts: tuple,
                      files: int, findings: int, units: int) -> Path:
    """The whole comparison in one file: every entry with its root causes, its
    facts, their lines and the code on them.

    One file, because the index printed on screen was read as the whole answer:
    an agent dropped 53 flagged units from rule names alone, without opening the
    detail written beside it or any of their code.
    """
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / "scan.txt"
    cache: dict[Path, list[str]] = {}
    body = [
        f"Rules compared with {LIST} -- {len(suspected)} unit(s) on your list -- "
        f"at {time.strftime('%H:%M')}.",
        f"Target {args.path}: {files} file(s) scanned, {units} unit(s) flagged, "
        f"{findings} finding(s).",
        "",
        *(f"Part {number}: {title.format(n=len(part))}."
          for number, (title, part) in enumerate(zip(PART_TITLES, parts), start=1)),
        "",
        "For every entry in parts 1 and 2, read the unit's code and decide for",
        f"yourself: add the unit, or the suspicion, to {LIST} if you agree; leave it",
        "if you do not. Each fact names the root causes it could be, as",
        "reference/README.md lists them; two labels on one fact are one thing to look",
        "at, not two. Within each part the units are in file and line order, which",
        "says nothing about which matter. Every unit starts with `== `.",
    ]
    for number, (title, part) in enumerate(zip(PART_TITLES, parts), start=1):
        body += ["", "#" * WIDTH, f"PART {number}: {title.format(n=len(part))}".upper(), "#" * WIDTH]
        if not part:
            body.append("\n(none)")
        for unit, shown in part:
            if number == 3:
                body.append(_render_agreement(unit, shown, suspected[unit["unit"]]))
            else:
                body.append(_render_unit(unit, shown, root, cache,
                                         suspected.get(unit["unit"])))
    body += ["", "-" * WIDTH, _CAVEATS]
    path.write_text("\n".join(body) + "\n")
    return path


def _summary(listing: Path, suspected: dict, parts: tuple, path: Path,
             files: int, units: int) -> str:
    """What the terminal shows: how many entries each part holds, and where they are."""
    lines = [f"Rules compared with {LIST} ({len(suspected)} unit(s) on it): "
             f"{files} file(s) scanned, {units} unit(s) flagged."]
    lines += [f"  part {number}: {title.format(n=len(part))}"
              for number, (title, part) in enumerate(zip(PART_TITLES, parts), start=1)]
    lines += ["",
              f"Everything is in {path} -- read it whole. For every entry in parts 1",
              f"and 2, read the unit's code and decide: add it to {LIST} if you agree,",
              "leave it if you do not."]
    if not os.access(listing, os.W_OK):
        lines += ["", f"{LIST} is read-only: step 1 is finished, so its list no longer changes."]
    return "\n".join(lines)


def _in_source_order(findings: list[UnitFindings], grouped: list[list[Finding]],
                     root: Path) -> list[tuple[int, Finding]]:
    """Every finding in the scan, as (unit index, finding): units by file and line,
    each unit's findings by line.

    Nothing is ranked. An order by what a root cause's repair saved elsewhere
    favoured the root causes with more, or easier, samples behind their
    average, so the list follows the code instead.
    """
    units = sorted(range(len(findings)), key=lambda index: (
        _relative(findings[index].unit.path, root), findings[index].unit.lineno))
    return [(index, finding) for index in units for finding in grouped[index]]


def _by_unit(shown: list[tuple[int, Finding]]) -> list[tuple[int, list[Finding]]]:
    """The findings regrouped by unit, units in order of their first finding."""
    order: dict[int, list[Finding]] = {}
    for index, finding in shown:
        order.setdefault(index, []).append(finding)
    return list(order.items())


def _describe(item: UnitFindings, shown: list[Finding], table: SignalTable,
              root: Path) -> dict:
    """One unit as a list of facts in line order, each tagged with what it could mean.

    The earlier shape nested evidence under each candidate root cause, which
    printed a fact once per root cause it routed to: one fact routing to two
    root causes became two identical paragraphs. The label is now an attribute
    of the fact rather than a heading above it, and each fact names the cards to
    settle it against.
    """
    findings = []
    for finding in shown:
        findings.append({
            "kind": finding.kind,
            "source": finding.source,
            "root_causes": [
                _label(rc, table) for rc in finding.root_causes
            ],
            "corroborated_by": list(finding.corroborated_by),
            "count": finding.count,
            "lines": list(finding.lines),
            "messages": [
                {"text": text, "lines": list(lines)} for text, lines in finding.messages
            ],
        })

    return {
        "unit": f"{_relative(item.unit.path, root)}::{item.unit.qualname}",
        "file": _relative(item.unit.path, root),
        "qualname": item.unit.qualname,
        "line": item.unit.lineno,
        "end_line": item.unit.end_lineno,
        "findings": findings,
        # The by-root-cause view, for anything asking what this unit could be an
        # instance of rather than what was seen in it.
        "candidates": [
            {"id": rc, "support": _support_summary(supporting)}
            for rc, supporting in rank_candidates(item.evidence, table)
        ],
    }


def _label(root_cause_id: str, table: SignalTable) -> dict:
    """A root cause as it appears on a finding: enough to open its card.

    Named beside the fact rather than in a block underneath it. The block held
    the repair and a verification note too, which was the card's own opening
    paragraph reprinted at the reader before they had opened it -- so they could
    act on the summary and never read the thing that says when not to.
    """
    node = table.root_causes.get(root_cause_id)
    if node is None:
        return {"id": root_cause_id, "name": "", "card": ""}
    return {"id": node.id, "name": node.name, "card": node.card}


def _support_summary(supporting: list) -> str:
    """"append_only_loop, index_based_iteration" -- which rules back this candidate."""
    return ", ".join(sorted({item.kind for item in supporting}))


def _relative(path: Path, root: Path) -> str:
    """Paths relative to the scan target, so output is short and portable."""
    base = root if root.is_dir() else root.parent
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


# -- readable rendering ----------------------------------------------------


WIDTH = 78


_CAVEATS = """What this output is and is not:
  - Every line is a fact about syntax. None of them is a verdict. Each of
    these shapes is the right thing to write somewhere, so the question is
    always whether it is right *here* -- which depends on what the code is
    for, and a rule cannot see that.
  - Every finding is listed, in one of the three parts, in file and line
    order within it. The order says nothing about which ones matter. Read
    in whatever order you think right.
  - The rules only recognise shapes somebody thought to describe in
    advance. Waste with no fixed shape leaves no trace here at all. What
    this output does not mention is not thereby absent, and no part of the
    taxonomy is ruled out by not appearing."""


def _render_unit(unit: dict, shown: list[dict], root: Path, cache: dict,
                 mine: set[str] | None) -> str:
    """One unit: every fact in `shown` once, each naming its root causes, with
    the code on its lines.

    The root causes sit on the fact rather than in a block below it. The block
    also carried each card's repair and a verification note, which is the card's
    own opening reprinted before the reader had opened it -- enough to act on,
    and no mention of when not to. The card path is here; the card is there.
    """
    lines = [
        "",
        "=" * WIDTH,
        f"== {unit['file']}:{unit['line']}  {unit['qualname']}  "
        f"(lines {unit['line']}-{unit['end_line']})",
    ]
    if mine is not None:
        lines.append(f"   on your list, suspected: {', '.join(sorted(mine)) or 'no root cause'}")

    for finding in shown:
        occurs = "" if finding["count"] == 1 else f"  x{finding['count']}"
        lines += [
            "",
            f"  {finding['kind']}{occurs}",
        ]
        if finding["corroborated_by"]:
            agree = ", ".join(finding["corroborated_by"])
            lines.append(f"         also reported by {agree}")
        for label in finding["root_causes"] or [{"id": "-", "name": "no card"}]:
            lines.append(f"         {label['id']:<7} {label['name']}")
        for message in finding["messages"]:
            lines.append(f"           {_wrap(message['text'], 11)}")
            lines.append(f"           at {_lines(message['lines'])}")
            lines += _code(Path(root, unit["file"]), message["lines"], cache)
    return "\n".join(lines)


def _render_agreement(unit: dict, shown: list[dict], mine: set[str]) -> str:
    """A unit where a rule agrees with the list: one line, as a second reason."""
    facts = ", ".join(
        f"{f['kind']} ({'/'.join(rc['id'] for rc in f['root_causes'] if rc['id'] in mine)})"
        for f in shown)
    return f"\n== {unit['unit']}  (lines {unit['line']}-{unit['end_line']}): {facts}"


def _code(path: Path, numbers: list[int], cache: dict) -> list[str]:
    """The source on these lines, numbered; past CODE_LINES, a count."""
    if path not in cache:
        try:
            cache[path] = path.read_text(errors="replace").splitlines()
        except OSError:
            cache[path] = []
    text = cache[path]
    wanted = [n for n in sorted(set(numbers)) if 1 <= n <= len(text)]
    out = [f"             {n:>5} | {text[n - 1].rstrip()[:140]}" for n in wanted[:CODE_LINES]]
    if len(wanted) > CODE_LINES:
        out.append(f"                   ... and {len(wanted) - CODE_LINES} more line(s)")
    return out


def _lines(numbers: list[int]) -> str:
    """"642, 668, 672 and 10 more" -- every line, without a wall of them."""
    shown = ", ".join(str(n) for n in numbers[:8])
    extra = len(numbers) - 8
    return f"{shown} and {extra} more" if extra > 0 else shown


def _wrap(text: str, indent: int) -> str:
    """Fold text to the report width, hanging continuation lines under `indent`.

    The caller has already written `indent` characters, so the first line is
    given the same indent and then stripped: that makes the fold account for the
    label sitting to its left instead of overrunning by its width.
    """
    return textwrap.fill(
        text, width=WIDTH, initial_indent=" " * indent, subsequent_indent=" " * indent
    ).lstrip()


if __name__ == "__main__":
    sys.exit(main())
