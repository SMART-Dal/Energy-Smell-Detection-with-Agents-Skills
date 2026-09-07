"""The types the static layer passes around: where code lives, and what was seen.

Kept next to the analyzers rather than beside the measurement types, because
these two halves never meet in code.  The static half produces `Evidence`; the
measurement half produces `Comparison`; the only place they come together is
the report the agent writes, which is why there is no type here for a claim or
a verdict.  Judging a smell is the agent's job, and this module deliberately
offers it no schema to hide behind.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class UnitRef:
    """An analysable chunk of code: usually a function, sometimes a whole class.

    A "unit" is the granularity at which a smell is judged, repaired and
    measured.  It is mostly a function or method; a class is also a unit,
    because waste sometimes lives in how several methods are arranged rather
    than inside any one of them.
    """

    path: Path
    qualname: str
    lineno: int
    end_lineno: int
    kind: str = "function"  # "function" | "method" | "class" | "module"
    attach_lineno: int = 0
    """First line that belongs to this unit, decorators included; 0 means `lineno`.

    `lineno` is the `def` line, which is what a reader wants to be sent to and
    where a unit's source starts.  It is not where a decorated unit *begins*:
    a linter reporting on the decorator lands above the `def`, inside the class
    body, and gets attributed to the class instead -- which is how B019, a rule
    this project maps and wires, produced nothing on any file ever scanned."""

    @property
    def first_lineno(self) -> int:
        return self.attach_lineno or self.lineno

    @property
    def slug(self) -> str:
        """Stable identifier, usable in filenames and cache keys."""
        return f"{self.path.name}::{self.qualname}"

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno} {self.qualname}"


@dataclass(frozen=True)
class Evidence:
    """One deterministic observation about a unit.

    Evidence is *not* a smell claim.  It is a fact ("there is a `str +=` inside
    a loop at line 12") plus the root causes that fact could plausibly
    indicate.  Turning evidence into a claim requires judging intent and
    context, which no analyzer can do, so no analyzer tries.
    """

    kind: str
    """Analyzer-defined signal name, e.g. "str_concat_in_loop"."""

    unit: UnitRef
    lineno: int
    suggests: tuple[str, ...]
    """Root-cause IDs this signal could indicate, e.g. ("C10.S4",)."""

    message: str
    """One-line human-readable description, shown in the scan report."""

    detail: dict = field(default_factory=dict, compare=False)
    """Analyzer-specific facts (loop depth, estimated trip count, ...).

    Left out of equality, and so out of the hash a frozen dataclass generates:
    a dict is unhashable, so putting two pieces of evidence in a set raised
    `TypeError` on a class that advertises itself as frozen.  Two observations
    of the same kind, at the same line, of the same unit are the same
    observation whatever an analyzer attached to them."""

    source: str = "ast"
    """Which analyzer family produced this, for the report to cite."""

    def __str__(self) -> str:
        return f"[{self.kind}] line {self.lineno}: {self.message}"
