"""What one line of `submissions.jsonl` must contain, checked before anything runs.

A submission is a repair proposed against a repository the agent did not edit.
It names the unit, gives the replacement source for the unit and for any callee
it changed, and gives the inputs. It never gives a `before`: that is read from
the repository, which is what stops a baseline being written to flatter the
result.

    {
      "id": "s1",
      "root_cause": "C5.S1",                  # absent when the arm has no taxonomy
      "unit": "src/app.py::tag_rows",         # path::qualname
      "changed": {"src/app.py::tag_rows": "def tag_rows(rows, blocked): ..."},
      "related": ["s2"],                      # other repairs of the same code
      "sole_caller_evidence": "...",          # required if a callee changed
      "equivalence": "returns_only",          # optional relaxation
      "cases_source": "def checks(): ...\\ndef cases(): ...",
      "notes": "...",                         # optional
      "agent_measurement": {...}              # written by verify.py, not by hand
    }

Every rule here is enforced with a message that says what to fix, because the
submission is written from scratch each time, by a model, and a malformed one
is the likeliest thing to go wrong in the whole pipeline.
"""

from __future__ import annotations

import hashlib
import json
import re

from .casefile import RELAXATIONS
from .splice import split_name

MEASURED_CASES = 5
"""`cases()` returns exactly this many inputs. Five, each making the unit behave
differently, is enough to show where a repair pays and where it does not, and
fixing the number keeps every submission's measurement the same length."""

ALLOWED = {
    "id", "root_cause", "unit", "changed", "related", "sole_caller_evidence",
    "equivalence", "cases_source", "notes", "agent_measurement",
}
REQUIRED = ("id", "unit", "changed", "cases_source")
RETIRED = {
    "file": "name the file inside `unit` instead: `src/app.py::Report.render`",
    "callees_changed": "every key of `changed` other than `unit` is a changed callee",
    "subsumed": "an identical repair is recorded as `same_repair_as` in findings.jsonl",
}
_ROOT_CAUSE = re.compile(r"^C\d{1,2}\.S\d{1,2}$")


def validate(record: dict) -> str | None:
    """The first thing wrong with one submission, or None."""
    if not isinstance(record, dict):
        return "each line must be a JSON object"
    for key in sorted(set(record) & set(RETIRED)):
        return f"`{key}` is no longer a field: {RETIRED[key]}"
    unknown = sorted(set(record) - ALLOWED)
    if unknown:
        return f"unknown field(s) {unknown}; allowed: {sorted(ALLOWED)}"
    missing = [key for key in REQUIRED if not record.get(key)]
    if missing:
        return f"missing or empty field(s): {missing}"
    if not isinstance(record["id"], str):
        return "`id` must be a string"

    try:
        split_name(record["unit"])
    except ValueError as exc:
        return f"`unit`: {exc}"

    changed = record["changed"]
    if not isinstance(changed, dict) or not all(
        isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in changed.items()
    ):
        return "`changed` must map `path::qualname` to the full replacement source"
    for name in changed:
        try:
            split_name(name)
        except ValueError as exc:
            return f"`changed` key: {exc}"
    if record["unit"] not in changed:
        return f"`changed` has no replacement for the unit itself ({record['unit']})"
    if len(changed) > 1 and not str(record.get("sole_caller_evidence") or "").strip():
        return (
            "`changed` touches more than the unit, so `sole_caller_evidence` is "
            "required: say how you established that nothing else calls or reads "
            "what you changed. Equivalence is checked on the unit only, so "
            "anything else broken by the change would pass every check here."
        )

    relaxation = record.get("equivalence", "strict")
    if relaxation not in RELAXATIONS:
        return f"`equivalence` must be one of {sorted(RELAXATIONS)}, not {relaxation!r}"
    related = record.get("related", [])
    if not isinstance(related, list) or not all(isinstance(r, str) for r in related):
        return "`related` must be a list of submission ids"
    if record["id"] in related:
        return "`related` lists the submission itself"
    root_cause = record.get("root_cause")
    if root_cause is not None and not (isinstance(root_cause, str)
                                       and _ROOT_CAUSE.match(root_cause)):
        return f"`root_cause` must be an ID such as C5.S1, not {root_cause!r}"
    if not isinstance(record["cases_source"], str):
        return "`cases_source` must be Python source text"
    return None


def validate_file(records: list[dict]) -> dict[str, str]:
    """Rules that span lines: unique ids, shared inputs, real cross-references.

    Every submission for one unit uses the same `cases_source`. That is what
    makes two repairs of the same function comparable -- each one's saving is
    measured on identical inputs -- and it is what lets the better of them be
    chosen when only one can be applied.
    """
    problems: dict[str, str] = {}
    ids = [r.get("id") for r in records if isinstance(r, dict)]
    duplicated = {i for i in ids if ids.count(i) > 1}
    by_unit: dict[str, set[str]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("unit") and isinstance(record.get("cases_source"), str):
            by_unit.setdefault(record["unit"], set()).add(record["cases_source"])

    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            continue
        sid = record["id"]
        if sid in duplicated:
            problems[sid] = f"id {sid!r} is used by more than one line"
        elif len(by_unit.get(record.get("unit"), ())) > 1:
            problems[sid] = (
                f"submissions for {record['unit']} do not share one `cases_source`; "
                f"every repair of a unit is measured on the same inputs"
            )
        else:
            dangling = sorted(set(record.get("related") or []) - set(ids))
            if dangling:
                problems[sid] = f"`related` names submissions that do not exist: {dangling}"
    return problems


def case_count_problem(cases: list[str], checks: list[str]) -> str | None:
    """`cases()` gives exactly five measured inputs; `checks()` at least one."""
    if len(cases) != MEASURED_CASES:
        return (f"`cases()` returned {len(cases)} inputs; it must return exactly "
                f"{MEASURED_CASES}, each making the unit behave differently")
    if not checks:
        return "`checks()` returned nothing; give the edge inputs for the equivalence check"
    return None


def submission_hash(record: dict) -> str:
    """Identity of a submission's content, ignoring its recorded measurement.

    Stored beside the measurement, so a line edited after it was measured is
    measured again, and a line that has not changed is not.
    """
    content = {k: v for k, v in record.items() if k != "agent_measurement"}
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def baseline_fingerprint(repo, record: dict) -> str:
    """Identity of the original code a submission was measured against.

    A digest of every file the submission names -- the unit's and each one in
    `changed` -- as `repo` holds them. Stored beside the measurement, so a
    number taken against an edited copy of the repository can be told apart
    from one taken against the repository itself: the review recomputes it on
    the pristine checkout, and a mismatch means `before` was not the real code.
    """
    paths = set()
    for name in [record.get("unit") or ""] + list(record.get("changed") or {}):
        try:
            paths.add(split_name(name)[0])
        except ValueError:
            continue
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode("utf-8") + b"\0")
        try:
            digest.update((repo / path).read_bytes())
        except OSError:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()[:16]
