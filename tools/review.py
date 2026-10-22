#!/usr/bin/env python3
"""Our side of a run: re-measure every submission, decide what to apply, report.

    python tools/review.py REPO RUN_DIR [--inputs DIR]  re-measure, decide, write the report
    python tools/review.py REPO RUN_DIR --apply         ...and write the applied repairs to REPO
    python tools/review.py REPO RUN_DIR --verdicts F    reuse a re-measurement already taken

RUN_DIR holds the agent's `submissions.jsonl` and `findings.jsonl` (its three
step files, joined). This writes `results.jsonl` and `REPORT.md` beside them.
It never ships inside a skill.

The agent measured its own repairs, and those numbers stay in its file as it
wrote them. The numbers that count are taken here, with the same fast profile,
on an idle machine, on a fresh copy of the repository, with `before` read from
the file rather than from anything the agent supplied, and on our own copy of
the generated inputs (`--inputs`) rather than the one the agent could reach. Where the two disagree,
and where a line was edited after the agent measured it, the report says so.

What gets applied: each submission was written against the original code, so
at most one per function can be. Among a function's `confirmed` submissions the
one with the highest mean saving across its four inputs is applied -- they share
their inputs, so the means are comparable -- and every other one is recorded
with the reason it was not. Nothing that is not `confirmed` is ever applied,
`mixed` included: it costs energy on some input, and which input the code sees
is not ours to decide.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lib.splice import splice_tree  # noqa: E402
from lib.submission import baseline_fingerprint, submission_hash  # noqa: E402

VERIFY = ROOT / "src" / "verify.py"
ORDER = ("confirmed", "partial", "mixed", "regressed", "negligible", "inconclusive",
         "not_equivalent", "invalid", "no_inputs", "error")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def remeasure(repo: Path, submissions: Path, inputs: Path | None) -> list[dict]:
    """Every submission, re-measured, without touching the agent's file.

    A line left `inconclusive` -- the host's noise floor too high to resolve
    anything -- is measured once more, after a fresh calibration: a passing
    burst of noise (Oct 21) left a 58% saving inconclusive here, minutes after
    the agent measured it on a 1.5% floor. The agent re-runs verify.py for such
    lines; the review, which runs once, did not.
    """
    with tempfile.TemporaryDirectory() as scratch:
        current = Path(scratch) / "submissions.jsonl"
        current.write_text(_without_retired(submissions), encoding="utf-8")
        results = _verify(repo, current, inputs)
    again = {r.get("id") for r in results if r.get("status") == "inconclusive"}
    if not again:
        return results
    lines = []
    for line in _without_retired(submissions).splitlines():
        try:
            if json.loads(line).get("id") in again:
                lines.append(line)
        except ValueError:
            continue
    with tempfile.TemporaryDirectory() as scratch:
        subset = Path(scratch) / "submissions.jsonl"
        subset.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        retried = {r.get("id"): {**r, "measured_twice": True}
                   for r in _verify(repo, subset, inputs)}
    return [retried.get(r.get("id"), r) for r in results]


RETIRED = ("equivalence", "equivalent")
"""Fields a submission could relax the check with until Oct 21. A run from before
is re-measured under today's rule -- everything compared -- so they are dropped
from the copy verify.py reads; the agent's own file is left as it was."""


def _without_retired(submissions: Path) -> str:
    out = []
    for line in submissions.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            out.append(line)            # verify.py reports it as it is
            continue
        if isinstance(record, dict):
            for key in RETIRED:
                record.pop(key, None)
        out.append(json.dumps(record))
    return "".join(line + "\n" for line in out)


def _verify(repo: Path, submissions: Path, inputs: Path | None) -> list[dict]:
    completed = subprocess.run(
        [sys.executable, str(VERIFY), str(submissions), "--repo", str(repo),
         "--no-record", "--json"] + (["--inputs", str(inputs)] if inputs else []),
        capture_output=True, text=True,
    )
    try:
        return json.loads(completed.stdout)
    except ValueError:
        raise SystemExit(f"re-measurement failed:\n{completed.stderr[-2000:]}")


def mean_saving(result: dict) -> float | None:
    """Mean percentage saved across the measured cases, from the joules."""
    savings = [100.0 * (c["before_energy_j"] - c["after_energy_j"]) / c["before_energy_j"]
               for c in result.get("per_case", []) if c.get("before_energy_j")]
    return statistics.mean(savings) if savings else None


def decide(submissions: list[dict], ours: dict[str, dict]) -> dict[str, dict]:
    """Which confirmed submission each function gets, and why the rest do not."""
    decisions: dict[str, dict] = {}
    claimed: dict[str, str] = {}          # path::qualname -> id of the applied submission
    by_unit: dict[str, list[dict]] = {}
    for record in submissions:
        result = ours.get(record["id"], {})
        if result.get("status") != "confirmed":
            decisions[record["id"]] = {
                "applied": False,
                "reason": f"not applied: {result.get('status', 'not measured')}",
            }
        else:
            by_unit.setdefault(record["unit"], []).append(record)

    for unit, group in by_unit.items():
        group.sort(key=lambda r: mean_saving(ours[r["id"]]) or 0.0, reverse=True)
        winner = None
        for record in group:
            names = set(record["changed"])
            taken = sorted(n for n in names if n in claimed)
            if winner is None and not taken:
                winner = record
                for name in names:
                    claimed[name] = record["id"]
                decisions[record["id"]] = {"applied": True, "reason": "applied: the largest "
                                           "mean saving among this function's confirmed repairs"}
                continue
            if winner is not None:
                linked = (record["id"] in winner.get("related", [])
                          or winner["id"] in record.get("related", []))
                reason = (f"not applied: an alternative repair of the same code as "
                          f"{winner['id']}, which saved more" if linked else
                          f"not applied: changes the same function as {winner['id']}, which "
                          f"is applied; both were written against the original, so only "
                          f"one can be")
            else:
                reason = (f"not applied: changes {', '.join(taken)}, which "
                          f"{claimed[taken[0]]} already changes")
            decisions[record["id"]] = {"applied": False, "reason": reason}
    return decisions


def write_report(path: Path, repo: Path, submissions: list[dict], findings: list[dict],
                 rows: list[dict]) -> None:
    listed = {f.get("unit") for f in findings if f.get("step") == 1}
    with_accepted = {f.get("unit") for f in findings if f.get("step") == 2
                     and any(isinstance(d, dict) and d.get("verdict") == "accepted"
                             for d in f.get("decisions") or [])}
    outcomes = [o for f in findings if f.get("step") == 3 for o in f.get("outcomes", [])]
    counts = {status: sum(r["status"] == status for r in rows) for status in ORDER}
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()

    out = [f"# Energy report — {repo.name}{' @ ' + commit if commit else ''}", ""]
    deferred = sum(o.get("outcome") == "deferred" for o in outcomes)
    out.append(f"{len(listed)} units listed, {len(listed & with_accepted)} with an accepted "
               f"suspicion · "
               f"{len(submissions)} repairs submitted, {deferred} deferred · "
               + " · ".join(f"{n} {s}" for s, n in counts.items() if n)
               + f" · {sum(r['applied'] for r in rows)} applied")
    measured = [r for r in rows if r.get("noise_floor_pct") is not None
                and r["status"] in ORDER[:6]]
    if measured:
        floors = [r["noise_floor_pct"] for r in measured]
        sources = sorted({r.get("floor_source") or "unknown" for r in measured})
        low, high = f"{min(floors):.1f}", f"{max(floors):.1f}"
        out.append(f"Noise floor {low if low == high else f'{low}–{high}'}% "
                   f"(from: {', '.join(sources)}).")
    out.append("")

    def section(title, chosen):
        if not chosen:
            return
        out.extend([f"## {title}", ""])
        for row in chosen:
            label = f"`{row['unit']}` — {row['id']}"
            if row.get("root_cause"):
                label += f" ({row['root_cause']})"
            out.append(f"### {label}")
            out.append("")
            out.append(f"**{row['status']}** — {row['reason']}")
            saving = row.get("mean_saving_pct")
            if saving is not None:
                out.append(f"Mean saving across its cases: {saving:+.1f}%.")
            if row.get("relaxed"):
                out.append("Behaviour compared under a relaxed rule: "
                           + "; ".join(note.rstrip(".") for note in row["relaxed"]) + ".")
            if row.get("stubbed"):
                out.append("Loaded with uninstalled packages stood in for: " + ", ".join(row["stubbed"]) + ".")
            if row["agent_status"] != row["status"]:
                out.append(f"The agent measured `{row['agent_status']}`; re-measured `{row['status']}`.")
            if not row["agent_line_unchanged"]:
                out.append("**This line was edited after the agent measured it.**")
            if row.get("agent_baseline_matches") is False:
                out.append("**The agent measured this against code that differs from the "
                           "repository's** -- its `--repo` held an edited copy -- so its "
                           "number is not about this code.")
            if row.get("skipped"):
                out.append("Loaded skipping failing top-level statements: "
                           + "; ".join(row["skipped"]) + ".")
            same = [o.get("label") for o in outcomes
                    if o.get("outcome") == "same_repair_as" and o.get("submission") == row["id"]]
            if same:
                out.append(f"Also the repair for suspicion(s) {', '.join(same)} of this unit.")
            if row.get("per_case"):
                # The +- and whether the verdict counted the case: a mean saving
                # above the floor whose pairs disagreed is not a saving, and the
                # table alone read as one (Oct 21).
                out.extend(["", "| case | before J | after J | saved | +- (95%) | counted |",
                            "|---|---:|---:|---:|---:|---|"])
                floor = row.get("noise_floor_pct") or 0.0
                for c in row["per_case"]:
                    b, a = c["before_energy_j"], c["after_energy_j"]
                    saved = 100 * (b - a) / b
                    ci = c.get("energy_ci_pct")
                    counted = ("no: pairs disagree" if c.get("significant") is False else
                               "no: within the floor" if abs(saved) <= floor else "yes")
                    out.append(f"| {c['label']} | {b:.2f} | {a:.2f} | {saved:+.1f}% | "
                               f"{'' if ci is None else f'{ci:.1f}%'} | {counted} |")
            out.append("")

    section("Applied", [r for r in rows if r["applied"]])
    section("Confirmed, not applied", [r for r in rows if r["status"] == "confirmed" and not r["applied"]])
    section("Measured, not confirmed", [r for r in rows if r["status"] in ORDER[1:6]])
    section("Not measured", [r for r in rows if r["status"] in ORDER[6:]])

    unmeasured = [(f["unit"], o) for f in findings if f.get("step") == 3
                  for o in f.get("outcomes", []) if o.get("outcome") in ("blocked", "deferred")]
    if unmeasured:
        out.extend(["## Detected, not measured", "",
                    "Accepted findings with no measurement: deferred beyond the repairs chosen "
                    "for measurement, or blocked.", ""])
        for unit, o in unmeasured:
            out.append(f"- `{unit}` {o.get('label')}: {o['outcome']} — {o.get('why')}")
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def _baseline_matches(repo: Path, record: dict) -> bool | None:
    stored = (record.get("agent_measurement") or {}).get("baseline_sha256")
    return None if not stored else stored == baseline_fingerprint(repo, record)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", type=Path)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--verdicts", type=Path,
                        help="a saved `verify.py --no-record --json` output to reuse")
    parser.add_argument("--inputs", type=Path,
                        help="our copy of the generated inputs (default: the repository's own)")
    parser.add_argument("--apply", action="store_true",
                        help="write the applied repairs into REPO")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    submissions_path = args.run_dir / "submissions.jsonl"
    submissions = read_jsonl(submissions_path)
    findings = read_jsonl(args.run_dir / "findings.jsonl")

    measured = (json.loads(args.verdicts.read_text()) if args.verdicts
                else remeasure(repo, submissions_path, args.inputs))
    (args.run_dir / "remeasured.json").write_text(json.dumps(measured, indent=1))
    ours = {r.get("id"): r for r in measured}

    valid = [r for r in submissions if isinstance(r.get("changed"), dict) and r.get("unit")]
    decisions = decide(valid, ours)

    rows = []
    for record in submissions:
        result = ours.get(record.get("id"), {"status": "error", "reason": "not re-measured"})
        decision = decisions.get(record.get("id"), {"applied": False,
                                                    "reason": "not applied: invalid"})
        rows.append({
            "id": record.get("id"),
            "unit": record.get("unit"),
            "root_cause": record.get("root_cause"),
            "status": result.get("status"),
            "reason": decision["reason"] if result.get("status") == "confirmed"
                      else result.get("reason", ""),
            "agent_status": (record.get("agent_measurement") or {}).get("status", "not measured"),
            # False when the line was edited after the agent measured it -- the
            # agent's number then belongs to a repair that is no longer there.
            "agent_line_unchanged": (record.get("agent_measurement") or {}).get(
                "submission_hash") == submission_hash(record),
            # False when the agent's `before` was not the repository's code: it
            # measured against an edited copy. None when it recorded no digest.
            "agent_baseline_matches": _baseline_matches(repo, record),
            "mean_saving_pct": mean_saving(result),
            "applied": decision["applied"],
            "not_applied_reason": None if decision["applied"] else decision["reason"],
            "related": record.get("related", []),
            "noise_floor_pct": result.get("noise_floor_pct"),
            "floor_source": result.get("noise_floor_from"),
            "relaxed": result.get("equivalence_relaxed", []),
            "stubbed": result.get("stubbed", []),
            "skipped": result.get("skipped_statements", []),
            "per_case": result.get("per_case", []),
        })

    (args.run_dir / "results.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    write_report(args.run_dir / "REPORT.md", repo, submissions, findings, rows)

    applied = [r for r in rows if r["applied"]]
    if args.apply and applied:
        changed = {}
        for record in submissions:
            if any(r["id"] == record["id"] for r in applied):
                changed.update(record["changed"])
        touched = splice_tree(repo, changed)
        print(f"applied {len(applied)} repair(s) to {', '.join(touched)}")
    for row in rows:
        print(f"{row['id']:<22} {row['status']:<15} "
              f"{'APPLIED' if row['applied'] else (row['not_applied_reason'] or '')[:70]}")
    print(f"\nwrote {args.run_dir / 'results.jsonl'} and {args.run_dir / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
