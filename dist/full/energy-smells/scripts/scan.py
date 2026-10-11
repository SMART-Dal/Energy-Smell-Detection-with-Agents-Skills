#!/usr/bin/env python3
"""Static evidence for energy smells: where to look, and what to look for.

    python scan.py PATH --units               ranked reading list, no findings
    python scan.py PATH                        an index: which units, how much
    python scan.py PATH --unit NAME            one unit in full
    python scan.py PATH --top 150 --json       machine-readable, more findings

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
           indicate.  Every finding is shown, dealt one rule at a time --
           see `_rank` -- and grouped by unit.  The order is a suggestion and
           nothing more.

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
from lib.signals import (  # noqa: E402
    Finding,
    SignalTable,
    group_findings,
    impact_of,
    load_signals,
    rank_candidates,
)

DETAIL_DIR = Path(".energy-scan")
"""Where the full report is written. Beside the caller's working directory
rather than beside the target, because the target is often somebody else's
repository and a scan should not leave anything in it."""

DEFAULT_UNITS = 15
"""How many units `--units` lists unless `--top` says otherwise."""



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
    parser.add_argument("--units", action="store_true",
                        help="rank units by how hot they look and stop there")
    parser.add_argument("--top", type=int, default=None,
                        help=f"how many findings to report (default: all), or "
                             f"with --units how many units to list (default "
                             f"{DEFAULT_UNITS})")
    parser.add_argument("--unit", metavar="NAME",
                        help="print one unit's findings in full and stop; "
                             "matches on qualified name, substring allowed")
    parser.add_argument("--out", type=Path, default=DETAIL_DIR,
                        help=f"where to write the full report "
                             f"(default {DETAIL_DIR}/)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of the readable report")
    parser.add_argument(
        "--cross-unit", action="store_true",
        help="let rules see that a unit runs inside a caller's loop, across "
             "files; off by default, and dropping it returns the scan to "
             "file-at-a-time exactly")
    args = parser.parse_args(argv)

    if not args.path.exists():
        parser.error(f"no such path: {args.path}")

    files = python_files(args.path)

    if args.units:
        # The reading list keeps units nothing flagged: its whole purpose is to
        # rank code before any rule has spoken.
        ranked = analyse_path(args.path, only_with_evidence=False,
                              cross_unit=args.cross_unit)
        report = {
            "target": str(args.path),
            "files_scanned": len(files),
            "units_found": len(ranked),
            "units": [_locate(item, args.path)
                      for item in ranked[: args.top or DEFAULT_UNITS]],
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

    findings = analyse_path(args.path, cross_unit=args.cross_unit)
    _report_rule_errors()
    table = load_signals()

    # A root cause whose repair never moved energy by the build's 15% line is
    # not reported, so neither is evidence that could only mean one of those.
    for item in findings:
        item.evidence = [e for e in item.evidence if table.reportable(e)]
    findings = [item for item in findings if item.evidence]

    grouped = [group_findings(item.evidence, table) for item in findings]
    if args.unit:
        described = [_describe(item, own, table, args.path)
                     for item, own in zip(findings, grouped)]
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

    ranked = _rank(findings, grouped, table)
    shown = ranked[: args.top] if args.top else ranked
    report = {
        "target": str(args.path),
        "files_scanned": len(files),
        "units_with_evidence": len(findings),
        "findings_total": len(ranked),
        "findings_shown": len(shown),
        "units": [_describe(findings[index], own, table, args.path)
                  for index, own in _by_unit(shown)],
    }

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
        (f"Findings for {report['target']} -- {report['findings_shown']} of "
         f"{report['findings_total']}, in {len(report['units'])} unit(s), dealt "
         f"one rule at a time so every rule appears early."),
        "Sections are `== file:line qualname`, so one unit can be cut out with",
        "grep or sed without reading the rest.",
        "",
        "Each fact names the root causes it could be. Their cards are at",
        "reference/root-causes/<ID>.md -- open one before accepting or rejecting",
        "anything. The order is pre-computed and is a suggestion, not a",
        "judgement about this code: read in whatever order you think right.",
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


def _rank(findings: list[UnitFindings], grouped: list[list[Finding]],
          table: SignalTable) -> list[tuple[int, Finding]]:
    """Every finding in the scan, as (unit index, finding), dealt one rule at a time.

    Sorting by measured saving alone put one rule's findings in a block: a
    repository with forty loop invariants showed forty of them before anything
    else. So the list is dealt like cards. Rules are taken in order of what
    their repairs saved when measured (`impact_of`), and each round takes the
    next finding of every rule that has one: the first finding of each rule,
    then the second, and so on. Every rule that fired is near the top, and a
    rule with many findings fills the tail rather than the head.

    Within a rule, the unit that runs deeper inside loops comes first, then
    the finding seen at more places.
    """
    by_kind: dict[str, list[tuple[int, Finding]]] = {}
    for index, own in enumerate(grouped):
        for finding in own:
            by_kind.setdefault(finding.kind, []).append((index, finding))
    for pairs in by_kind.values():
        pairs.sort(key=lambda pair: (
            -findings[pair[0]].reached_at_depth,
            -pair[1].count,
            str(findings[pair[0]].unit.path),
            pair[1].lines[0] if pair[1].lines else 0,
        ))
    order = sorted(by_kind, key=lambda kind: (
        -max(impact_of(f.root_causes, table) for _, f in by_kind[kind]), kind))

    ranked: list[tuple[int, Finding]] = []
    for depth in range(max((len(pairs) for pairs in by_kind.values()), default=0)):
        ranked += [by_kind[kind][depth] for kind in order if depth < len(by_kind[kind])]
    return ranked


def _by_unit(shown: list[tuple[int, Finding]]) -> list[tuple[int, list[Finding]]]:
    """The findings regrouped by unit, units in order of their first finding."""
    order: dict[int, list[Finding]] = {}
    for index, finding in shown:
        order.setdefault(index, []).append(finding)
    return list(order.items())


def _describe(item: UnitFindings, shown: list[Finding], table: SignalTable,
              root: Path) -> dict:
    """One unit as a worth-ordered list of facts, each tagged with what it could mean.

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
        "hotness": _hotness_dict(item),
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


def _hotness_dict(item: UnitFindings) -> dict:
    """Static hotness proxies. A guess about frequency, never a measurement."""
    return {
        "unit_file": str(item.unit.path),
        "own_loop_depth": item.max_repeat_depth,
        "reached_at_depth": item.reached_at_depth,
        "fan_in": item.fan_in,
        "fan_out": len(item.fan_out),
        "called_from": [
            {"caller": site.caller, "line": site.line,
             "repeat_depth": site.repeat_depth, "file": site.file}
            for site in item.called_from
        ],
    }


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
    for and how often it runs, neither of which a rule can see.
  - The order deals one rule at a time, rules in the order of what their
    repairs saved when we measured them on other code, so every rule that
    fired appears near the top. It is a starting point and not a claim
    about this code: a small repair in a loop that runs a billion times
    beats a large one that runs twice, and only you can see which is which
    here. Read in whatever order you think right.
  - Root causes whose repairs never changed energy by 15% either way, on
    any input we measured, are not reported at all.
  - The rules only recognise shapes somebody thought to describe in
    advance. Waste with no fixed shape leaves no trace here at all. What
    this output does not mention is not thereby absent, and no part of the
    taxonomy is ruled out by not appearing."""


def _render_index(report: dict, detail: Path) -> str:
    """What is where, and how to open it -- deliberately without the findings.

    The index has to be enough to choose a unit and not enough to write a
    finding from, because a reader given the findings up front stops reading the
    code and starts confirming the list.
    """
    lines = [
        f"{report['files_scanned']} file(s)  |  "
        f"{report['units_with_evidence']} unit(s) with evidence  |  "
        f"{report['findings_total']} finding(s)",
        f"showing {report['findings_shown']}, dealt one rule at a time so every "
        f"rule appears early",
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

    # One line a unit: every unit with a finding is listed, so the index is
    # kept to where it is and what fired. How it is reached is in the detail.
    for rank, unit in enumerate(report["units"], start=1):
        depth = unit["hotness"]["reached_at_depth"]
        kinds = ", ".join(_headline(f) for f in unit["findings"])
        lines.append(f"{rank:>4}. " + _wrap(f"{unit['file']}:{unit['line']}  "
                                           f"{unit['qualname']}  (depth {depth}): {kinds}", 6))

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


def _render_unit(unit: dict) -> str:
    """One unit in full: every fact once, worth-ordered, each naming its cards.

    The root causes sit on the fact rather than in a block below it. The block
    also carried each card's repair and a verification note, which is the card's
    own opening reprinted before the reader had opened it -- enough to act on,
    and no mention of when not to. The card path is here; the card is there.
    """
    lines = [
        "",
        "=" * WIDTH,
        f"== {unit['file']}:{unit['line']}  {unit['qualname']}",
        f"   {unit['end_line'] - unit['line'] + 1} lines | {_hotness(unit['hotness'])}",
    ]

    for finding in unit["findings"]:
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
        sites = [s for s in hotness["called_from"] if s["repeat_depth"] > 0]
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
        # Callers and call sites are different numbers and the reader counts the
        # second: two calls from one function is one caller, and printing only
        # "3 place(s)" beside four visible calls reads as a lost edge.
        sites = len(hotness["called_from"])
        callers = hotness["fan_in"]
        elsewhere = {
            site["caller"] for site in hotness["called_from"]
            if site.get("file") and site["file"] != hotness.get("unit_file")
        }
        where = f", {len(elsewhere)} in other file(s)" if elsewhere else ""
        counted = (f"{callers} caller(s)" if sites == callers
                   else f"{callers} caller(s), {sites} call site(s)")
        parts.append(f"called from {counted}{where}")
    return " | ".join(parts)


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
