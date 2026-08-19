"""Splitting a Python file into analysable units.

A *unit* is the granularity at which a smell is judged, repaired and
measured.  Usually that is a function or a method.  Classes are
also emitted as units, because a few root causes only make sense across several
methods at once (C2.S3 excessive modularization in a hot path, C9.S3 N+1 query
patterns, C11.* concurrency smells).

Nested functions are emitted too: a closure defined inside a loop is exactly the
kind of thing C3.S3 is about, and it needs to be addressable on its own.
"""

from __future__ import annotations

import ast
from pathlib import Path

from .models import UnitRef

FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def parse_file(path: Path) -> ast.Module | None:
    """Parse a source file, returning None if it cannot be read or parsed.

    Unparseable files are common in the wild (Python 2 leftovers, templates
    with a .py extension), and one bad file must not stop a repository scan.
    """
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return None


def iter_units(path: Path, tree: ast.Module) -> list[tuple[UnitRef, ast.AST]]:
    """List every unit in a parsed module, paired with its AST node.

    Returned in source order.  The qualified name follows Python's own
    convention (`Outer.method`, `outer.<locals>.inner` becomes `outer.inner`
    for readability, since we only need it to be unique and recognisable).
    """
    units: list[tuple[UnitRef, ast.AST]] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, FUNCTION_NODES):
                qualname = f"{prefix}{child.name}"
                units.append((_make_ref(path, child, qualname, _function_kind(prefix)), child))
                visit(child, f"{qualname}.")
            elif isinstance(child, ast.ClassDef):
                qualname = f"{prefix}{child.name}"
                units.append((_make_ref(path, child, qualname, "class"), child))
                visit(child, f"{qualname}.")
            else:
                # Keep descending: functions can hide inside `if`, `try`, `with`.
                visit(child, prefix)

    visit(tree, "")
    units.sort(key=lambda pair: pair[0].lineno)
    return units


def _function_kind(prefix: str) -> str:
    """A function directly inside a class body is a method; otherwise plain."""
    return "method" if prefix and not prefix.endswith(".<locals>.") else "function"


def _make_ref(path: Path, node: ast.AST, qualname: str, kind: str) -> UnitRef:
    return UnitRef(
        path=path,
        qualname=qualname,
        lineno=node.lineno,
        end_lineno=getattr(node, "end_lineno", node.lineno) or node.lineno,
        kind=kind,
    )


def unit_source(source: str, unit: UnitRef) -> str:
    """Extract a unit's own source text, preserving its original indentation."""
    lines = source.splitlines()
    return "\n".join(lines[unit.lineno - 1 : unit.end_lineno])
