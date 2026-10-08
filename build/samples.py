"""A card's repair examples, read from the samples we measured.

Nothing about a repair is typed into the catalog except an optional note. The
case file under `validation/taxonomy/` gives the code, `before` and `after`
with the helpers they need; `validation/alignment/decisions.yaml` gives the
title (the case file's docstring when it is not listed there); and the latest
run in `validation/results/taxonomy.jsonl` gives what each case measured. So
the example the agent reads, the code that was measured and the result the
card states cannot drift apart.

The result line ends with one of four actions, explained once in SKILL.md:

    saved on some or all cases, nothing cost more      Apply the after.
    cost more on some case (saving or not elsewhere)   Try both directions.
    nothing moved on any case                          Report it; no need to measure.
    the run could not resolve it                       Measure it.

A regression never means the root cause is wrong. The taxonomy is the
reference; a few inputs on one host cannot overturn it, and the same repair
can pay or cost depending on the code around it. What a regression changes is
the advice: try the other direction too, and let the measurement decide.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "validation" / "taxonomy"
RESULTS = ROOT / "validation" / "results" / "taxonomy.jsonl"
DECISIONS = ROOT / "validation" / "alignment" / "decisions.yaml"
RULE_TESTS = ROOT / "tests" / "rules"


@dataclass(frozen=True)
class Measured:
    """One sample: its code, and what each of its cases measured."""

    before: str
    after: str
    verdicts: tuple[tuple[str, str], ...]
    """(case label, "confirmed" | "regressed" | "negligible"), in case order."""
    status: str
    """The sample's overall verdict in the run, e.g. `confirmed`, `inconclusive`."""


def _names_used(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def extract(path: Path) -> tuple[str, str]:
    """`before` and `after` from a case file, each with the helpers it needs."""
    source = path.read_text()
    tree = ast.parse(source)
    defined: dict[str, ast.stmt] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined[target.id] = node
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]

    def closure(entry: str) -> list[ast.stmt]:
        wanted, queue = set(), [entry]
        while queue:
            name = queue.pop()
            if name in wanted or name not in defined:
                continue
            wanted.add(name)
            queue.extend(n for n in _names_used(defined[name]) if n in defined)
        wanted.discard(entry)
        nodes = {id(defined[w]) for w in wanted}
        return [n for n in tree.body if id(n) in nodes] + [defined[entry]]

    def render(entry: str) -> str:
        body = closure(entry)
        needed = {n for stmt in body for n in _names_used(stmt)}
        lines = [ast.get_source_segment(source, imp) for imp in imports
                 if {(a.asname or a.name).split(".")[0] for a in imp.names} & needed]
        blocks = (["\n".join(lines)] if lines else []) + \
                 [ast.get_source_segment(source, stmt) for stmt in body]
        return "\n\n\n".join(b for b in blocks if b).strip() + "\n"

    return render("before"), render("after")


@lru_cache(maxsize=None)
def _results() -> dict[str, dict]:
    """The latest run, by case-file stem."""
    rows = {}
    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[Path(row["case_file"]).stem] = row
    return rows


def _case_verdict(case: dict, floor: float) -> str:
    before, after = case["before_energy_j"], case["after_energy_j"]
    saving = 100.0 * (before - after) / before if before else 0.0
    if case.get("significant") and saving > floor:
        return "confirmed"
    if case.get("significant") and -saving > floor:
        return "regressed"
    return "negligible"


def measured(stem: str) -> Measured:
    path = CASES / f"{stem}.py"
    if not path.exists():
        raise FileNotFoundError(f"no case file validation/taxonomy/{stem}.py")
    before, after = extract(path)
    row = _results().get(stem)
    if row is None:
        return Measured(before, after, (), "not measured")
    floor = row.get("noise_floor_pct") or 0.0
    verdicts = tuple((c["label"], _case_verdict(c, floor)) for c in row.get("per_case", []))
    return Measured(before, after, verdicts, row["status"])


@lru_cache(maxsize=None)
def _decisions() -> dict[str, list[dict]]:
    import yaml
    raw = yaml.safe_load(DECISIONS.read_text()) or {}
    return {rid: block.get("examples", []) for rid, block in raw.items()}


def case_files(root_cause_id: str) -> list[str]:
    """Every sample filed under a root cause: decisions.yaml's order, then the rest."""
    prefix = root_cause_id.replace(".", "") + "_"
    on_disk = sorted(path.stem for path in CASES.glob(f"{prefix}*.py"))
    listed = [e["file"] for e in _decisions().get(root_cause_id, []) if e["file"] in on_disk]
    return listed + [stem for stem in on_disk if stem not in listed]


def title_of(stem: str) -> str:
    """The sample's title: decisions.yaml's, else its docstring's first line after `--`.

    Some samples are listed under a second root cause as well; the title used
    is the one under the root cause the sample is filed as.
    """
    own = stem.split("_")[0].replace("S", ".S")
    for example in _decisions().get(own, []):
        if example["file"] == stem:
            return example["title"]
    doc = ast.get_docstring(ast.parse((CASES / f"{stem}.py").read_text())) or ""
    first = doc.splitlines()[0] if doc else ""
    if " -- " not in first:
        raise KeyError(f"{stem} has no title in decisions.yaml and no `--` docstring line")
    return first.split(" -- ", 1)[1].strip().rstrip(".")


def rule_negative(reference: str) -> str:
    """Why `<rule>/<function>` is not a negative in that rule's fixtures, or ''."""
    rule, _, function = reference.partition("/")
    cases = RULE_TESTS / rule / "test_cases.py"
    main = RULE_TESTS / rule / "test_main.py"
    if not cases.exists():
        return f"no rule fixtures at tests/rules/{rule}/"
    defined = {node.name for node in ast.walk(ast.parse(cases.read_text()))
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    if function not in defined:
        return f"tests/rules/{rule}/test_cases.py defines no {function}"
    positives: set[str] = set()
    for node in ast.walk(ast.parse(main.read_text())):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
                and any(isinstance(t, ast.Name) and t.id == "EXPECTED" for t in node.targets)):
            positives = {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    if function in positives:
        return f"{function} is a positive in tests/rules/{rule}, not a negative"
    return ""


def _labels(verdicts, kind: str) -> str:
    return ", ".join(f"`{label}`" for label, v in verdicts if v == kind)


def decision(sample: Measured) -> str:
    """One line: what each case measured, then the action SKILL.md explains."""
    v = sample.verdicts
    if sample.status in ("inconclusive", "timeout", "error", "not measured") or not v:
        return "**Measured:** our host could not resolve it. **Measure it.**"
    kinds = {k for _, k in v}
    saved, cost, flat = _labels(v, "confirmed"), _labels(v, "regressed"), _labels(v, "negligible")
    parts = [f"less energy on {saved}" if saved else "",
             f"more on {cost}" if cost and saved else f"more energy on {cost}" if cost else "",
             f"no change on {flat}" if flat else ""]
    measured_text = "; ".join(part for part in parts if part)
    if kinds == {"negligible"}:
        return f"**Measured:** no change on any case ({flat}). **Report it; no need to measure.**"
    if "regressed" in kinds:
        return f"**Measured:** {measured_text}. **Try both directions.**"
    return f"**Measured:** {measured_text}. **Apply the after.**"
