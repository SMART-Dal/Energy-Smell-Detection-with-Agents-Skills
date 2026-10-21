"""What one line of `submissions.jsonl` must contain, checked before anything runs.

A submission is a repair proposed against a repository the agent did not edit.
It names the unit and gives the replacement source for the unit and for any
callee it changed. It never gives a `before`, which is read from the
repository, and never gives the inputs, which are generated for the unit
outside the session (see lib/inputs.py): either one written by the agent could
be shaped to flatter the result.

    {
      "id": "s1",
      "root_cause": "C5.S1",                  # absent when the arm has no taxonomy
      "unit": "src/app.py::tag_rows",         # path::qualname
      "changed": {"src/app.py::tag_rows": "def tag_rows(rows, blocked): ..."},
      "related": ["s2"],                      # other repairs of the same code, or []
      "sole_caller_evidence": "...",          # null unless a callee changed
      "notes": "...",                         # or ""
      "agent_measurement": {...}              # written by verify.py, not by hand
    }

Every rule here is enforced with a message that says what to fix, because the
submission is written from scratch each time, by a model, and a malformed one
is the likeliest thing to go wrong in the whole pipeline.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
import re

from .splice import split_name

MEASURED_CASES = 4
"""`cases()` returns exactly this many inputs, and a repair is confirmed only if
it saves energy on every one of them. Four, each making the unit do different
work, is enough to show where a repair pays and where it does not; fixing the
number keeps every measurement the same length and every verdict the same bar
(Javad, Oct 2026)."""

ALLOWED = {
    "id", "root_cause", "unit", "changed", "related", "sole_caller_evidence",
    "notes", "agent_measurement",
}
REQUIRED = ("id", "unit", "changed")
RETIRED = {
    "file": "name the file inside `unit` instead: `src/app.py::Report.render`",
    "callees_changed": "every key of `changed` other than `unit` is a changed callee",
    "subsumed": "an identical repair is recorded as `same_repair_as` in step4.jsonl",
    "cases_source": "the inputs are generated for you: request them with inputs.py, and "
                    "drop the field",
    # Oct 21: the check can no longer be relaxed by the submission. Everything a
    # call does is compared for every repair; a repair that needs a weaker check
    # changes behaviour that callers can see.
    "equivalence": "the check is no longer relaxed for any repair: drop the field. Return "
                   "value, arguments, printed and logged output, files and module- and "
                   "class-level state are all compared",
    "equivalent": "a repair can no longer supply its own comparison: drop the field. The "
                  "return values are compared as they are",
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

    related = record.get("related", [])
    if not isinstance(related, list) or not all(isinstance(r, str) for r in related):
        return "`related` must be a list of submission ids"
    if record["id"] in related:
        return "`related` lists the submission itself"
    root_cause = record.get("root_cause")
    if root_cause is not None and not (isinstance(root_cause, str)
                                       and _ROOT_CAUSE.match(root_cause)):
        return f"`root_cause` must be an ID such as C5.S1, not {root_cause!r}"
    return None


_MOCKING = {"mock", "unittest.mock", "pytest_mock"}
_PLAIN_BASES = {"NamedTuple", "TypedDict", "Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"}
"""Bases a class in the inputs may have besides built-in types: shapes for data."""


def replaced_code(source: str) -> str | None:
    """Does this source -- generated inputs -- swap code for its own?
    The first case, or None.

    A unit that calls the network or a native library cannot run here, and
    the temptation is to replace that call: `module.fetch = fake`, or an
    object assembled with `obj.process = lambda *a: 0`. Then the measurement
    times the fake, and the saving is a fraction of something nobody runs --
    one run reported 68% that way, of a wrapper whose real work is native.
    So assigning a lambda, or a function defined here, onto any attribute or
    through `setattr` or `types.MethodType`, and importing a mocking library,
    are refused. So is a class here that inherits from anything but a built-in
    type and defines methods: a `TPostman` subclass whose `get` returned canned
    JSON stood in for an HTTP client in one generated input. Data put on a
    module or object -- `pricing.args = namespace` -- is input, and allowed.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None                     # reported when the source is run
    defined = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def is_code(value) -> bool:
        return isinstance(value, ast.Lambda) or (
            isinstance(value, ast.Name) and value.id in defined)

    def plain_base(base) -> bool:
        name = base.id if isinstance(base, ast.Name) else \
            base.attr if isinstance(base, ast.Attribute) else None
        return name in _PLAIN_BASES or isinstance(getattr(builtins, name or "", None), type)

    def binds_method(value) -> bool:
        func = getattr(value, "func", None)
        return isinstance(value, ast.Call) and (
            isinstance(func, ast.Attribute) and func.attr == "MethodType"
            or isinstance(func, ast.Name) and func.id == "MethodType")

    found = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if methods and not all(plain_base(b) for b in node.bases):
                found = node
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            module = node.module if isinstance(node, ast.ImportFrom) else None
            if module in _MOCKING or any(n in _MOCKING for n in names) or \
                    (module == "unittest" and "mock" in names):
                found = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is not None and (is_code(node.value) or binds_method(node.value)) and \
                    any(isinstance(t, ast.Attribute) for t in targets):
                found = node
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "setattr" and len(node.args) == 3 \
                and is_code(node.args[2]):
            found = node
        if found is not None:
            line = source.splitlines()[found.lineno - 1].strip()
            return (f"this source replaces code, at line {found.lineno}: `{line[:80]}`. "
                    f"Everything measured has to run the real code -- a replaced function, a "
                    f"subclass overriding a method, or a mock measures something nobody runs.")
    return None


def validate_file(records: list[dict]) -> dict[str, str]:
    """Rules that span lines: unique ids and real cross-references.

    Every repair of one unit is measured on that unit's generated inputs, so
    two repairs of the same function are always compared on identical inputs.
    """
    problems: dict[str, str] = {}
    ids = [r.get("id") for r in records if isinstance(r, dict)]
    duplicated = {i for i in ids if ids.count(i) > 1}

    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            continue
        sid = record["id"]
        if sid in duplicated:
            problems[sid] = f"id {sid!r} is used by more than one line"
        else:
            dangling = sorted(set(record.get("related") or []) - set(ids))
            if dangling:
                problems[sid] = f"`related` names submissions that do not exist: {dangling}"
    return problems


def case_count_problem(cases: list[str], checks: list[str]) -> str | None:
    """`cases()` gives exactly MEASURED_CASES measured inputs; `checks()` at least one."""
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
