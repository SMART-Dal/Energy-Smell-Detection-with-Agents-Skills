#!/usr/bin/env python3
"""Static evidence for energy smells: where to look, and what to look for.

    python scan.py PATH --units               ranked reading list, no findings
    python scan.py PATH                        an index: which units, how much
    python scan.py PATH --unit NAME            one unit in full
    python scan.py PATH --top 40 --json        machine-readable, more units

The default prints an **index**, not the findings.  Tool output is not something
a reader can put down: it is read in full, once, before anything is known about
the code, and a scan that empties itself into the transcript spends its reader's
attention on whichever rule happened to fire most.  So the default says which
units carry what, writes the detail to a file, and leaves opening it to the
reader -- who by then has a reason to prefer one unit over another.

Two different questions, deliberately kept apart:

  --units  answers "which functions are worth my time?".  It ranks every unit
           in the target by how hot it looks -- loop nesting, including the
           nesting of its callers, and how many places call it -- and says
           nothing at all about what might be wrong with them.  Run this first
           and read the code yourself.

  default  answers "what did the rules notice?".  It reports *facts* -- "a
           string is grown with += inside a loop at line 45" -- one entry per
           rule per unit, tagged with every root cause that fact could
           indicate, ordered by what the repair is worth rather than by how
           many times the rule fired.

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
from lib.signals import (  # noqa: E402
    SignalTable,
    budget,
    group_findings,
    impact_of,
    load_signals,
    rank_candidates,
    score,
)

STRENGTH_ORDER = [Strength.DEFINITE, Strength.LIKELY, Strength.CONTEXTUAL]

DETAIL_DIR = Path(".energy-scan")
"""Where the full report is written. Beside the caller's working directory
rather than beside the target, because the target is often somebody else's
repository and a scan should not leave anything in it."""

DEPTH_WEIGHT = 4
"""How much one level of loop nesting is worth when ordering units.

Deliberately the same as one definite finding: a fact that is certainly true is
worth about as much as the difference between code that runs once and code that
runs inside a loop. Both are guesses, and the ordering only has to be roughly
right for the reader to start in a sensible place."""


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
    parser.add_argument("--unit", metavar="NAME",
                        help="print one unit's findings in full and stop; "
                             "matches on qualified name, substring allowed")
    parser.add_argument("--out", type=Path, default=DETAIL_DIR,
                        help=f"where to write the full report "
                             f"(default {DETAIL_DIR}/)")
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

    described = sorted(
        (_describe(item, table, args.path) for item in findings),
        key=lambda unit: (-unit["score"], unit["file"], unit["line"]),
    )
    report = {
        "target": str(args.path),
        "files_scanned": len(files),
        "units_with_evidence": len(described),
        "units": described[: args.top],
    }

    if args.unit:
        wanted = [u for u in described if u["qualname"] == args.unit]
        # Substring is the convenience; an exact name must never drag in the
        # nested helpers that happen to contain it.
        wanted = wanted or [u for u in described if args.unit in u["unit"]]
        if not wanted:
            parser.error(
                f"no unit matching {args.unit!r} has evidence. Run without "
                f"--unit for the index of the ones that do."
            )
        print("\n".join(_render_unit(unit) for unit in wanted))
        return 0

    if args.json:
        json.dump(report, sys.stdout, indent=1)
        print()
        return 0

    detail = _write_detail(report, args.out, args.path)
    print(_render_index(report, detail))
    return 0


def _write_detail(report: dict, out: Path, target: Path) -> Path:
    """Every unit in full, on disk, for the reader who wants one of them.

    Written unconditionally rather than on request: the index is only honest if
    the thing it points at already exists, and a reader who has to re-run the
    scan to see a finding will read the index as the whole answer instead.
    """
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{target.name or 'scan'}.txt"
    body = [
        f"Full findings for {report['target']} -- "
        f"{report['units_with_evidence']} unit(s) with evidence.",
        "Sections are `== file:line qualname`, so one unit can be cut out with",
        "grep or sed without reading the rest.",
    ]
    body += [_render_unit(unit) for unit in report["units"]]
    body += ["", "-" * WIDTH, _CAVEATS]
    path.write_text("\n".join(body) + "\n")
    return path


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
    """One unit as a worth-ordered list of facts, each tagged with what it could mean.

    The earlier shape nested evidence under each candidate root cause, which
    printed a fact once per root cause it routed to: `repeated_lookup_in_loop`
    reaches both C8.S3 and C10.S5, so seven lookups became fourteen identical
    paragraphs. The label is now an attribute of the fact rather than a heading
    above it, and the cards to read are listed once at the end of the unit.
    """
    grouped = group_findings(item.evidence, table)
    allowance = budget(item.unit.end_lineno - item.unit.lineno + 1)
    shown, over = grouped[:allowance], grouped[allowance:]

    findings = []
    for finding in shown:
        findings.append({
            "kind": finding.kind,
            "source": finding.source,
            "strength": finding.strength.value,
            "root_causes": list(finding.root_causes),
            "corroborated_by": list(finding.corroborated_by),
            "count": finding.count,
            "lines": list(finding.lines),
            "score": score(finding.strength, impact_of(finding.root_causes, table)),
            "messages": [
                {"text": text, "lines": list(lines)} for text, lines in finding.messages
            ],
        })

    named = sorted({rc for f in shown for rc in f.root_causes})
    return {
        "unit": f"{_relative(item.unit.path, root)}::{item.unit.qualname}",
        "file": _relative(item.unit.path, root),
        "qualname": item.unit.qualname,
        "line": item.unit.lineno,
        "end_line": item.unit.end_lineno,
        "hotness": _hotness_dict(item),
        "score": (
            sum(f["score"] for f in findings)
            + DEPTH_WEIGHT * item.reached_at_depth
        ),
        "findings": findings,
        "over_budget": [
            {"kind": f.kind, "count": f.count, "lines": list(f.lines)} for f in over
        ],
        "cards": [_card(table.root_causes[rc]) for rc in named if rc in table],
        # The by-root-cause view, for anything asking what this unit could be an
        # instance of rather than what was seen in it.
        "candidates": [
            {"id": rc, "support": _support_summary(supporting)}
            for rc, supporting in rank_candidates(item.evidence, table)
        ],
    }


def _card(node) -> dict:
    """What a reader needs to open one root cause and act on it."""
    return {
        "id": node.id,
        "name": node.name,
        "card": node.card,
        "repair": node.repair,
        "measurability": node.measurability,
        "advisory_only": node.advisory_only,
        "impact": node.impact,
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


def _support_summary(supporting: list) -> str:
    """"1 definite, 2 likely" -- how strongly this candidate is backed."""
    counts = {s: 0 for s in STRENGTH_ORDER}
    for item in supporting:
        counts[item.strength] += 1
    return ", ".join(
        f"{count} {strength.value}" for strength, count in counts.items() if count
    )


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
    for and how often it runs. `contextual` marks the ones where that
    judgement does most of the work.
  - `worth` is the measured saving of this repair in code that also does
    other work, bucketed. It orders the list; it does not decide anything.
    A `low` fact in a loop that runs a billion times still beats a `high`
    one that runs twice, and only you can see which is which.
  - The rules only recognise shapes somebody thought to describe in
    advance. Waste with no fixed shape leaves no trace here at all. What
    this output does not mention is not thereby absent, and no part of the
    taxonomy is ruled out by not appearing."""


IMPACT_WORD = {4: "high", 3: "medium", 2: "low", 1: "unmeasured"}


def _render_index(report: dict, detail: Path) -> str:
    """What is where, and how to open it -- deliberately without the findings.

    The index has to be enough to choose a unit and not enough to write a
    finding from, because a reader given the findings up front stops reading the
    code and starts confirming the list.
    """
    lines = [
        f"{report['files_scanned']} file(s)  |  "
        f"{report['units_with_evidence']} unit(s) with evidence  |  "
        f"showing {len(report['units'])}",
        "=" * WIDTH,
    ]

    if not report["units"]:
        return "\n".join(lines + [
            "",
            "No rule fired anywhere in this target.",
            "",
            "That is a fact about the rules, not a verdict about the code. The rules",
            "recognise fixed syntactic shapes; waste that does not take one of those",
            "shapes is invisible to them however expensive it is. Read the code.",
        ])

    for rank, unit in enumerate(report["units"], start=1):
        span = unit["end_line"] - unit["line"] + 1
        lines += ["", f"{rank:>3}. {unit['file']}:{unit['line']}  {unit['qualname']}"]
        lines.append(f"     {span} lines | {_hotness(unit['hotness'])}")
        lines.append(f"     {_tally(unit)}")
        headline = ", ".join(_headline(f) for f in unit["findings"][:3])
        if headline:
            lines.append(f"     {_wrap('top: ' + headline, 5)}")

    lines += [
        "",
        "-" * WIDTH,
        f"FULL DETAIL: {detail}",
        f"ONE UNIT:    scan.py {report['target']} --unit {report['units'][0]['qualname']}",
        "",
        "NEXT: read the units above in this order, forming your own view of what",
        "is wasteful in each. Open a unit's findings when you have one -- they are",
        "there to be argued with, not to be transcribed.",
    ]
    return "\n".join(lines)


def _headline(finding: dict) -> str:
    """"repeated_lookup_in_loop x7" -- the rule and how often, not what it means."""
    return finding["kind"] + ("" if finding["count"] == 1 else f" x{finding['count']}")


def _tally(unit: dict) -> str:
    """"8 findings across 31 lines -- 1 definite, 3 likely"."""
    counts = {s.value: 0 for s in STRENGTH_ORDER}
    for finding in unit["findings"]:
        counts[finding["strength"]] += 1
    breakdown = ", ".join(f"{n} {name}" for name, n in counts.items() if n)
    places = sum(f["count"] for f in unit["findings"])
    held = len(unit["over_budget"])
    tail = f"; {held} more not shown" if held else ""
    return (
        f"{len(unit['findings'])} finding(s) at {places} place(s) "
        f"-- {breakdown}{tail}"
    )


def _render_unit(unit: dict) -> str:
    """One unit in full: every fact once, worth-ordered, then the cards to read."""
    lines = [
        "",
        "=" * WIDTH,
        f"== {unit['file']}:{unit['line']}  {unit['qualname']}",
        f"   {unit['end_line'] - unit['line'] + 1} lines | {_hotness(unit['hotness'])}",
    ]

    for finding in unit["findings"]:
        labels = " / ".join(finding["root_causes"]) or "-"
        occurs = "" if finding["count"] == 1 else f"  x{finding['count']}"
        lines += [
            "",
            f"  {finding['strength']:<10} {finding['kind']:<28} {labels}{occurs}",
        ]
        if finding["corroborated_by"]:
            agree = ", ".join(finding["corroborated_by"])
            lines.append(f"      also reported by {agree}")
        for message in finding["messages"]:
            lines.append(f"      {_wrap(message['text'], 6)}")
            lines.append(f"      at {_lines(message['lines'])}")

    if unit["over_budget"]:
        lines += ["", "  over budget, named only:"]
        for held in unit["over_budget"]:
            lines.append(f"      {held['kind']} at {_lines(held['lines'])}")

    if unit["cards"]:
        lines += ["", "  cards to settle these against:"]
        for card in unit["cards"]:
            worth = IMPACT_WORD.get(card["impact"], "unmeasured")
            lines.append(f"      {card['id']:<7} {card['name']}   worth: {worth}")
            for label, value in (
                ("read", card["card"]),
                ("repair", card["repair"]),
                ("verify", _verify_note(card)),
            ):
                prefix = f"              {label:<8}"
                lines.append(prefix + _wrap(value, len(prefix)))
    return "\n".join(lines)


def _lines(numbers: list[int]) -> str:
    """"642, 668, 672 and 10 more" -- every line, without a wall of them."""
    shown = ", ".join(str(n) for n in numbers[:8])
    extra = len(numbers) - 8
    return f"{shown} and {extra} more" if extra > 0 else shown


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
