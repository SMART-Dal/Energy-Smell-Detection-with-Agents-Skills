#!/usr/bin/env python3
"""Build submissions.jsonl from repair specs. Each changed function is taken from the
repository as it stands, the listed replacements are applied, and the result is dedented
to column zero. Nothing outside the listed replacements changes."""
import ast
import json
import sys

REPO = "/home/javad/energy-run/dx-toolkit"


def func_text(path, qualname):
    src = open(REPO + "/" + path).read()
    lines = src.splitlines(keepends=True)
    node = ast.parse(src)
    body = node.body
    target = None
    for part in qualname.split("."):
        found = None
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.name == part:
                found = n
                break
        if found is None:
            raise SystemExit("not found: %s::%s" % (path, qualname))
        target = found
        body = found.body
    start = min([d.lineno for d in target.decorator_list] + [target.lineno]) - 1
    end = target.end_lineno
    text = "".join(lines[start:end])
    indent = target.col_offset
    out = []
    for line in text.splitlines(keepends=True):
        out.append(line[indent:] if line.startswith(" " * indent) else line)
    return "".join(out), "".join(lines[start:end])


def apply(indented, replacements, label):
    text = indented
    for old, new in replacements:
        n = text.count(old)
        if n != 1:
            raise SystemExit("%s: expected one match, found %d for %r" % (label, n, old[:60]))
        text = text.replace(old, new)
    return text


def build(spec):
    changed = {}
    for f in spec["funcs"]:
        path, qual = f["unit"].split("::")
        dedented, original_indented = func_text(path, qual)
        # apply replacements against the indented original, then dedent
        indented_new = apply(original_indented, f["replacements"], spec["id"])
        lines = []
        indent = None
        for line in indented_new.splitlines(keepends=True):
            if indent is None and line.strip():
                indent = len(line) - len(line.lstrip(" "))
            lines.append(line[indent:] if indent and line.startswith(" " * indent) else line)
        changed[f["unit"]] = "".join(lines)
    return {
        "id": spec["id"],
        "unit": spec["unit"],
        "changed": changed,
        "sole_caller_evidence": spec["sole_caller_evidence"],
        "notes": spec.get("notes", ""),
    }


if __name__ == "__main__":
    import specs
    out = []
    for spec in specs.SPECS:
        out.append(build(spec))
    with open(REPO + "/submissions.jsonl", "w") as fh:
        for rec in out:
            fh.write(json.dumps(rec) + "\n")
    print("wrote", len(out), "submissions")
