#!/usr/bin/env python3
"""Static evidence for energy smells: where to look, and what to look for.

    python scan.py PATH --units               ranked reading list, no findings
    python scan.py PATH                        top 15 units with their evidence
    python scan.py PATH --top 40 --json        machine-readable, more units

Two different questions, deliberately kept apart:

  --units  answers "which functions are worth my time?".  It ranks every unit
           in the target by how hot it looks -- loop nesting, including the
           nesting of its callers, and how many places call it -- and says
           nothing at all about what might be wrong with them.  Run this first
           and read the code yourself.

  default  answers "what did the rules notice?".  It reports *facts* -- "a
           string is grown with += inside a loop at line 45" -- grouped under
           the root causes those facts could indicate.

Nothing here ever says a smell is present.  Whether a fact is a smell depends
on what the code is for, how hot it is, and what the author was required to do,
none of which an analyzer can see.  That judgement belongs to the reader.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.analysis.engine import (  # noqa: E402
    UnitFindings,
    analyse_path,
    available_analyzers,
    python_files,
)
from lib.analysis.models import Strength  # noqa: E402
from lib.signals import SignalTable, load_signals, rank_candidates  # noqa: E402

STRENGTH_ORDER = [Strength.DEFINITE, Strength.LIKELY, Strength.CONTEXTUAL]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="a .py file or a directory tree")
    parser.add_argument("--units", action="store_true",
                        help="rank units by how hot they look and stop there")
    parser.add_argument("--top", type=int, default=15,
                        help="how many units to report (default 15)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of the readable report")
    args = parser.parse_args(argv)

    if not args.path.exists():
        parser.error(f"no such path: {args.path}")

    files = python_files(args.path)

    if args.units:
        # The reading list keeps units nothing flagged: its whole purpose is to
        # rank code before any rule has spoken.
        ranked = analyse_path(args.path, only_with_evidence=False)
        report = {
            "target": str(args.path),
            "files_scanned": len(files),
            "units_found": len(ranked),
            "units": [_locate(item, args.path) for item in ranked[: args.top]],
        }
        print(json.dumps(report, indent=1) if args.json else _render_units(report))
        return 0

    analyzers = available_analyzers()
    runnable = [name for name, blocked in analyzers.items() if blocked is None]
    if not runnable:
        # Each family explains its own absence, so this message stays the same
        # whatever families the installation happens to have.
        blockers = "\n  ".join(
            f"{name}: {why}" for name, why in analyzers.items()
        ) or "none are installed"
        parser.error(
            f"nothing can be analysed on this machine, so the scan would be "
            f"silently empty rather than clean:\n  {blockers}\n"
            f"`--units` still works -- it needs no analyzer."
        )
    for name, why in analyzers.items():
        if why is not None:
            print(f"note: skipping {name} -- {why}", file=sys.stderr)

    findings = analyse_path(args.path)
    table = load_signals()

    report = {
        "target": str(args.path),
        "files_scanned": len(files),
        "units_with_evidence": len(findings),
        "units": [
            _describe(item, table, args.path) for item in findings[: args.top]
        ],
    }

    if args.json:
        json.dump(report, sys.stdout, indent=1)
        print()
    else:
        print(_render(report))
    return 0


def _locate(item: UnitFindings, root: Path) -> dict:
    """One unit's position and hotness, with nothing about its contents."""
    return {
        "unit": f"{_relative(item.unit.path, root)}::{item.unit.qualname}",
        "file": _relative(item.unit.path, root),
        "qualname": item.unit.qualname,
        "line": item.unit.lineno,
        "end_line": item.unit.end_lineno,
        "hotness": _hotness_dict(item),
    }


def _describe(item: UnitFindings, table: SignalTable, root: Path) -> dict:
    """One unit, as a list of candidate root causes each carrying its own evidence.

    Evidence is nested *under* the root cause it supports rather than listed
    beside it.  Read apart, the two lists say that some root cause is a
    candidate without saying which line produced that belief, leaving the
    reader to re-derive a link the routing table already knew.

    Two consequences of nesting, both intended.  One root cause usually
    collects several pieces of evidence, and how many and how strong they are
    is the point of the `because` line.  And one piece of evidence often
    appears under more than one root cause -- that is not duplication but a
    genuine ambiguity, which the cards' neighbour sections exist to settle.
    """
    candidates = []
    for root_cause_id, supporting in rank_candidates(item.evidence, table):
        node = table.root_causes[root_cause_id]
        candidates.append({
            "id": node.id,
            "name": node.name,
            "category": node.category,
            "category_name": node.category_name,
            "card": node.card,
            "repair": node.repair,
            "measurability": node.measurability,
            "advisory_only": node.advisory_only,
            "support": _support_summary(supporting),
            "evidence": [_evidence_dict(e) for e in sorted(supporting, key=_evidence_order)],
        })

    return {
        "unit": f"{_relative(item.unit.path, root)}::{item.unit.qualname}",
        "file": _relative(item.unit.path, root),
        "qualname": item.unit.qualname,
        "line": item.unit.lineno,
        "end_line": item.unit.end_lineno,
        "hotness": _hotness_dict(item),
        "candidates": candidates,
    }


def _hotness_dict(item: UnitFindings) -> dict:
    """Static hotness proxies. A guess about frequency, never a measurement."""
    return {
        "own_loop_depth": item.max_loop_depth,
        "reached_at_depth": item.reached_at_depth,
        "fan_in": item.fan_in,
        "fan_out": len(item.fan_out),
        "called_from": [
            {"caller": site.caller, "line": site.line, "loop_depth": site.loop_depth}
            for site in item.called_from
        ],
    }


def _evidence_dict(evidence) -> dict:
    return {
        "kind": evidence.kind,
        "line": evidence.lineno,
        "strength": evidence.strength.value,
        "message": evidence.message,
        "source": evidence.source,
    }


def _support_summary(supporting: list) -> str:
    """"1 definite, 2 likely" -- how strongly this candidate is backed."""
    counts = {s: 0 for s in STRENGTH_ORDER}
    for item in supporting:
        counts[item.strength] += 1
    return ", ".join(
        f"{count} {strength.value}" for strength, count in counts.items() if count
    )


def _evidence_order(evidence) -> tuple[int, int]:
    """Strongest first, then by line, so the reader meets the facts that matter."""
    return (STRENGTH_ORDER.index(evidence.strength), evidence.lineno)


def _relative(path: Path, root: Path) -> str:
    """Paths relative to the scan target, so output is short and portable."""
    base = root if root.is_dir() else root.parent
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


# -- readable rendering ----------------------------------------------------


WIDTH = 78


def _render(report: dict) -> str:
    """The readable report: one block per unit, one sub-block per candidate.

    Laid out so that everything needed to act on a candidate -- what to read,
    what the repair is, whether it can be measured, and which lines caused the
    suspicion -- sits together under that candidate's heading.
    """
    header = (
        f"{report['files_scanned']} files  |  "
        f"{report['units_with_evidence']} units with evidence  |  "
        f"showing {len(report['units'])}"
    )
    lines = [header, "=" * WIDTH]

    if not report["units"]:
        lines += [
            "",
            "No rule fired anywhere in this target.",
            "",
            "That is a fact about the rules, not a verdict about the code. The rules",
            "recognise fixed syntactic shapes; waste that does not take one of those",
            "shapes is invisible to them however expensive it is. Read the code.",
        ]
        return "\n".join(lines)

    for rank, unit in enumerate(report["units"], start=1):
        lines += ["", f"{rank:>3}. {unit['file']}:{unit['line']}  {unit['qualname']}"]
        lines.append(f"     {_hotness(unit['hotness'])}")

        for candidate in unit["candidates"]:
            lines += ["", f"     {candidate['id']}  {candidate['name']}"]
            lines.append(_field("read", candidate["card"]))
            lines.append(_field("repair", candidate["repair"]))
            lines.append(_field("verify", _verify_note(candidate)))
            lines.append(_field("because", f"({candidate['support']})"))
            for item in candidate["evidence"]:
                prefix = f"         {item['strength']:<10} line {item['line']:<5} "
                lines.append(prefix + _wrap(item["message"], len(prefix)))
                lines.append(" " * len(prefix) + f"[{item['source']}/{item['kind']}]")

    lines += [
        "",
        "-" * WIDTH,
        "NEXT: merge this into the suspicions you formed by reading the code, then",
        "open the cards listed under `read` and settle each candidate against that",
        "unit's actual source. Do not write a finding from this output alone.",
        "",
        "What this output is and is not:",
        "  - Every line above is a fact about syntax. None of them is a verdict.",
        "    Each of these shapes is the right thing to write somewhere, so the",
        "    question is always whether it is right *here* -- which depends on what",
        "    the code is for and how often it runs. `contextual` marks the ones",
        "    where that judgement does most of the work.",
        "  - The rules only recognise shapes somebody thought to describe in",
        "    advance. Waste with no fixed shape leaves no trace here at all. What",
        "    this output does not mention is not thereby absent, and no part of the",
        "    taxonomy is ruled out by not appearing.",
    ]
    return "\n".join(lines)


def _render_units(report: dict) -> str:
    """The ranked reading list: where to spend attention, and why."""
    lines = [
        f"{report['files_scanned']} files  |  {report['units_found']} units  |  "
        f"showing the {len(report['units'])} that look hottest",
        "=" * WIDTH,
    ]
    for rank, unit in enumerate(report["units"], start=1):
        lines.append(f"{rank:>3}. {unit['file']}:{unit['line']}  {unit['qualname']}")
        lines.append(f"     {_hotness(unit['hotness'])}")

    lines += [
        "",
        "-" * WIDTH,
        "Ranked by how often the code is likely to run: loop nesting, the nesting",
        "of the callers that reach it, and how many places call it. That is a",
        "static guess. It cannot see how many times a loop actually trips, which",
        "branches are taken, or anything about calls from other files -- so treat",
        "the order as a suggestion and override it when you know better.",
        "",
        "NEXT: read these units. Form your own view of what is wasteful in them",
        "before consulting anything else.",
    ]
    return "\n".join(lines)


def _hotness(hotness: dict) -> str:
    """One line on why this unit ranked where it did."""
    parts = [f"loop depth {hotness['own_loop_depth']}"]
    if hotness["reached_at_depth"] > hotness["own_loop_depth"]:
        sites = [s for s in hotness["called_from"] if s["loop_depth"] > 0]
        # Naming every caller of a widely used helper turns one line into ten,
        # and the reader only needs somewhere to start following the chain.
        shown = ", ".join(f"{s['caller']}:{s['line']}" for s in sites[:3])
        if len(sites) > 3:
            shown += f" and {len(sites) - 3} more"
        parts.append(
            f"but runs at depth {hotness['reached_at_depth']} "
            f"via {shown or 'its callers'}"
        )
    if hotness["fan_in"]:
        parts.append(f"called from {hotness['fan_in']} place(s) in this file")
    return " | ".join(parts)


def _verify_note(candidate: dict) -> str:
    """Whether a claim of this root cause can be settled by measurement."""
    if candidate["advisory_only"]:
        return (
            "advisory only -- the repair is correct but too small to measure, "
            "so report it without a verdict"
        )
    return f"{candidate['measurability']} -- measurable, so a claim here must be verified"


def _field(label: str, value: str) -> str:
    """One `label   value` line inside a candidate block, wrapped to width."""
    prefix = f"       {label:<9}"
    return prefix + _wrap(value, len(prefix))


def _wrap(text: str, indent: int) -> str:
    """Fold text to the report width, hanging continuation lines under `indent`."""
    return textwrap.fill(
        text, width=WIDTH, initial_indent="", subsequent_indent=" " * indent
    ).lstrip()


if __name__ == "__main__":
    sys.exit(main())
