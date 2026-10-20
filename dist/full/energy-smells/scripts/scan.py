#!/usr/bin/env python3
"""Static evidence for energy smells: what the rules noticed, and where.

    python scan.py PATH                        an index: which units, how much
    python scan.py PATH --unit NAME            one unit in full
    python scan.py PATH --top 150 --json       machine-readable, more findings

The default prints an **index**, not the findings.  Tool output is not something
a reader can put down: it is read in full, once, before anything is known about
the code, and a scan that empties itself into the transcript spends its reader's
attention on whichever rule happened to fire most.  So the default says which
units carry what, writes the detail to a file, and leaves opening it to the
reader -- who by then has a reason to prefer one unit over another.

It reports *facts* -- "a string is grown with += inside a loop at line 45" --
one entry per rule per unit, tagged with every root cause that fact could
indicate.  Every finding is shown, grouped by unit, in file and line order.  The
order says nothing about which ones matter; which code to read, and in what
order, is the reader's to decide.

Nothing here ever says a smell is present.  Whether a fact is a smell depends
on what the code is for and what the author was required to do, neither of
which an analyzer can see.  That judgement belongs to the reader.
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
    load_signals,
    rank_candidates,
)

DETAIL_DIR = Path(".energy-scan")
"""Where the full report is written. Beside the caller's working directory
rather than beside the target, because the target is often somebody else's
repository and a scan should not leave anything in it."""


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
            f"silently empty rather than clean:\n  {blockers}"
        )
    for name, why in analyzers.items():
        if why is not None:
            print(f"note: skipping {name} -- {why}", file=sys.stderr)

    findings = analyse_path(args.path, cross_unit=args.cross_unit,
                            only_with_evidence=not args.unit)
    _report_rule_errors()
    table = load_signals()
    scanned = findings
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
            # Two different answers, which one message used to blur: an agent
            # read "no unit ... has evidence" as a wrong name and tried three.
            names = [f"{_relative(item.unit.path, args.path)}::{item.unit.qualname}"
                     for item in scanned]
            quiet = [n for n in names if n.split("::", 1)[1] == args.unit] or \
                    [n for n in names if args.unit in n]
            if quiet:
                print("\n".join(f"{name}: no rule fired on it." for name in quiet[:5]))
                print("That is a fact about the rules, not a verdict about the code: "
                      "read it yourself.")
                return 0
            parser.error(
                f"no unit named {args.unit!r} in {args.path}. Give it as the index "
                f"prints it -- `path/to/file.py::Qualname`, or just `Qualname`."
            )
        print("\n".join(_render_unit(unit) for unit in wanted))
        return 0

    ordered = _in_source_order(findings, grouped, args.path)
    shown = ordered[: args.top] if args.top else ordered
    report = {
        "target": str(args.path),
        "files_scanned": len(files),
        "units_with_evidence": len(findings),
        "findings_total": len(ordered),
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
         f"{report['findings_total']}, in {len(report['units'])} unit(s), in "
         f"file and line order."),
        "Sections are `== file:line qualname`, so one unit can be cut out with",
        "grep or sed without reading the rest.",
        "",
        "Each fact names the root causes it could be. Their cards are at",
        "reference/root-causes/<ID>.md -- open one before accepting or rejecting",
        "anything. The order is the order of the code and says nothing about",
        "which findings matter: read in whatever order you think right.",
    ]
    body += [_render_unit(unit) for unit in report["units"]]
    body += ["", "-" * WIDTH, _CAVEATS]
    path.write_text("\n".join(body) + "\n")
    return path


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
  - Every finding is listed, in file and line order. The order says
    nothing about which ones matter. Read in whatever order you think right.
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
        f"showing {report['findings_shown']}, in file and line order",
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
    for number, unit in enumerate(report["units"], start=1):
        kinds = ", ".join(_headline(f) for f in unit["findings"])
        lines.append(f"{number:>4}. " + _wrap(f"{unit['file']}:{unit['line']}  "
                                           f"{unit['qualname']}: {kinds}", 6))

    lines += [
        "",
        "-" * WIDTH,
        f"FULL DETAIL: {detail}",
        f"ONE UNIT:    scan.py {report['target']} --unit {report['units'][0]['qualname']}",
        "",
        "NEXT: read the units above, in whatever order you think right, forming",
        "your own view of what is wasteful in each. Open a unit's findings when",
        "you have one -- they are there to be argued with, not to be transcribed.",
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
        f"   {unit['end_line'] - unit['line'] + 1} lines",
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
