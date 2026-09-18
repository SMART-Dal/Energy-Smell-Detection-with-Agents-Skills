#!/usr/bin/env python3
"""Rewrite each card's repair examples from the case files that were measured.

    python validation/alignment/apply.py            # check, print a diff summary
    python validation/alignment/apply.py --write    # edit catalog/*.yaml

The point is that every repair example a model reads has been executed and
measured, rather than written by hand and assumed. `decisions.yaml` says which
case file backs which example; the code shown on the card is then lifted from
that file rather than maintained separately, so the two cannot drift.

What is lifted is `before`, `after`, and only the module-level helpers those
two actually reference -- transitively, so a helper calling a helper brings its
own. What is left behind is `cases()` and anything only `cases()` uses, because
input construction is measurement scaffolding and teaches nothing about the
repair.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
TAXONOMY = ROOT / "validation" / "taxonomy"
CATALOG = ROOT / "catalog"
DECISIONS = Path(__file__).resolve().parent / "decisions.yaml"


def _names_used(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)
    }


def _top_level(tree: ast.Module) -> dict[str, ast.stmt]:
    """Module-level definitions and constants, by the name they bind."""
    found: dict[str, ast.stmt] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found[node.name] = node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node
    return found


def extract(path: Path) -> tuple[str, str]:
    """(before, after) source, each carrying the helpers it needs."""
    source = path.read_text()
    tree = ast.parse(source)
    defined = _top_level(tree)
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]

    def closure(entry: str) -> list[ast.stmt]:
        """`entry` plus every module-level definition it reaches."""
        wanted, queue = set(), [entry]
        while queue:
            name = queue.pop()
            if name in wanted or name not in defined:
                continue
            wanted.add(name)
            queue.extend(n for n in _names_used(defined[name]) if n in defined)
        wanted.discard(entry)
        # Source order keeps helpers reading the way they were written.
        ordered = [n for n in tree.body if n in {defined[w] for w in wanted}]
        return ordered + [defined[entry]]

    def render(entry: str) -> str:
        blocks = []
        needed = {n for stmt in closure(entry) for n in _names_used(stmt)}
        for imp in imports:
            bound = {(a.asname or a.name).split(".")[0] for a in imp.names}
            if bound & needed:
                blocks.append(ast.get_source_segment(source, imp))
        blocks += [ast.get_source_segment(source, s) for s in closure(entry)]
        return "\n\n\n".join(b for b in blocks if b).strip() + "\n"

    return render("before"), render("after")


# Case file docstrings open by naming the root cause they belong to, which is
# already the heading the example sits under on the card. Titles contain
# hyphens of their own ("Runtime-Management"), so the cut is at the first
# spaced double dash rather than at any dash.
_OPENER = re.compile(r"^C\d+\.S\d+\b")


def _note_from_docstring(path: Path) -> str:
    """The case file's own account of why the shape is worth measuring."""
    doc = (ast.get_docstring(ast.parse(path.read_text())) or "").strip()
    if _OPENER.match(doc):
        head, sep, rest = doc.partition(" -- ")
        if sep and "\n\n" not in head:
            doc = rest.lstrip()
    if not doc:
        return ""
    # What follows the dash is the back half of the docstring's opening
    # sentence, so it starts lower case and reads as a fragment on the card.
    return doc[:1].upper() + doc[1:] if doc else doc


def provenance(file_stem: str) -> str:
    return f"Measured in `validation/taxonomy/{file_stem}.py`."


def rebuild(rc: dict, spec: dict, old_by_title: dict) -> list[dict]:
    """The card's examples, with code taken from the measured case files."""
    out = []
    for entry in spec["examples"]:
        stem = entry["file"]
        path = TAXONOMY / f"{stem}.py"
        if not path.exists():
            raise SystemExit(f"{rc['id']}: no case file {path}")
        before, after = extract(path)

        # Keep the note the card already had wherever the example survives;
        # a shape promoted from the suite takes the case file's own docstring,
        # which is where its reason for existing was written down.
        note = old_by_title.get(entry["title"])
        if note is None and entry.get("note"):
            note = entry["note"]
        if note is None:
            note = _note_from_docstring(path)
        note = note.rstrip()
        if "validation/taxonomy/" not in note:
            note = f"{note}\n\n{provenance(stem)}" if note else provenance(stem)

        out.append({
            "title": entry["title"],
            "before": before,
            "after": after,
            "note": note + "\n",
        })
    return out


class _Dumper(yaml.SafeDumper):
    pass


def _str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_presenter)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--only", default="", help="category prefix, e.g. C1")
    args = parser.parse_args()

    decisions = yaml.safe_load(DECISIONS.read_text()) or {}
    touched = 0
    for path in sorted(CATALOG.glob("C*.yaml")):
        category = yaml.safe_load(path.read_text())
        changed = False
        for rc in category:
            spec = decisions.get(rc["id"])
            if not spec:
                continue
            if args.only and not rc["id"].startswith(args.only + "."):
                continue
            examples = (rc.get("refactoring") or {}).get("examples") or []
            old_by_title = {e.get("title"): (e.get("note") or "").rstrip()
                            for e in examples}
            rebuilt = rebuild(rc, spec, old_by_title)
            print(f"{rc['id']:<8} {len(examples)} -> {len(rebuilt)} examples   "
                  + ", ".join(e["file"] for e in spec["examples"]))
            rc["refactoring"]["examples"] = rebuilt
            changed = True
            touched += 1
        if changed and args.write:
            path.write_text(yaml.dump(category, Dumper=_Dumper, sort_keys=False,
                                      width=88, allow_unicode=True))
    print(f"\n{touched} root causes {'rewritten' if args.write else 'would be rewritten'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
