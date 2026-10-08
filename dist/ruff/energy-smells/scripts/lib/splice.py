"""Replace named functions in a file, leaving everything else byte-identical.

A submission carries ordinary Python source, never an AST and never a diff.
This module is the one place that parses: it finds where each named function
lives and swaps those lines. Comments, imports, class bodies and every function
nobody named come through untouched, which is what lets the `before` side be
the repository's own code and the `after` side differ from it by the repair
alone.

Names are `path::qualname` everywhere outside this module -- `src/app.py::
Report.render` -- so one submission can change a unit and a callee that lives
in another file. Inside, `splice()` works on one file's text with bare
qualnames, and `splice_tree()` groups by path.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path


def split_name(name: str) -> tuple[str, str]:
    """`src/app.py::Report.render` -> (`src/app.py`, `Report.render`)."""
    path, sep, qualname = name.partition("::")
    if not sep or not path.endswith(".py") or not qualname:
        raise ValueError(
            f"{name!r} is not `path/to/file.py::qualname` "
            f"(for example `src/app.py::Report.render`)"
        )
    return path, qualname


def spans(source: str) -> dict[str, tuple[int, int]]:
    """qualname -> (start, end) line indices, 0-based and half-open.

    The span starts at the first decorator, so replacing a decorated function
    replaces its decorators too instead of leaving them stranded above the new
    body. A replacement therefore has to carry the decorators it wants.
    """
    found: dict[str, tuple[int, int]] = {}

    def walk(node, prefix: str = "") -> None:
        for child in getattr(node, "body", []):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                first = min([child.lineno] + [d.lineno for d in child.decorator_list])
                found[name] = (first - 1, child.end_lineno)
                if isinstance(child, ast.ClassDef):
                    walk(child, prefix=name + ".")

    walk(ast.parse(source))
    return found


def splice(source: str, changed: dict[str, str]) -> str:
    """`source` with each named function replaced by the supplied text.

    The replacement is dedented and then indented to where the original sat,
    so a method can be written at column zero. Raises `KeyError` for a name
    the file does not define and `SyntaxError` if the result does not parse.
    """
    table = spans(source)
    missing = sorted(set(changed) - set(table))
    if missing:
        raise KeyError(f"not defined in this file: {missing}")

    lines = source.splitlines(keepends=True)
    # Bottom-up, so spans above the one being replaced keep their line numbers.
    for name in sorted(changed, key=lambda n: -table[n][0]):
        start, end = table[name]
        indent = " " * (len(lines[start]) - len(lines[start].lstrip()))
        body = "\n".join(
            indent + line if line.strip() else ""
            for line in textwrap.dedent(changed[name]).strip("\n").splitlines()
        )
        lines[start:end] = [body + "\n"]

    spliced = "".join(lines)
    ast.parse(spliced)
    return spliced


def splice_tree(root: Path, changed: dict[str, str]) -> list[str]:
    """Apply `path::qualname -> source` to the files under `root`, in place.

    Every file is spliced in memory first and written only once all of them
    succeeded, so a bad replacement never leaves the tree half-patched.
    Returns the relative paths that were rewritten.
    """
    root = Path(root).resolve()
    by_file: dict[str, dict[str, str]] = {}
    for name, text in changed.items():
        path, qualname = split_name(name)
        by_file.setdefault(path, {})[qualname] = text

    patched: dict[Path, str] = {}
    for path, replacements in by_file.items():
        target = (root / path).resolve()
        if root not in target.parents or not target.is_file():
            raise FileNotFoundError(f"no such file in the repository: {path}")
        patched[target] = splice(target.read_text(encoding="utf-8"), replacements)

    for target, text in patched.items():
        target.write_text(text, encoding="utf-8")
    return sorted(by_file)
