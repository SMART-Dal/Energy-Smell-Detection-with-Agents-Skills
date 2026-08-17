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
from enum import Enum
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

    @property
    def slug(self) -> str:
        """Stable identifier, usable in filenames and cache keys."""
        return f"{self.path.name}::{self.qualname}"

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno} {self.qualname}"


class Strength(str, Enum):
    """How much a piece of evidence, on its own, implies an actual smell.

    Every analyzer reports facts it is certain about -- the difference is how
    far the fact goes toward being a *smell*.  A mutable default argument is
    essentially always wrong.  A one-line delegating wrapper is only wrong on a
    hot path, and is good design everywhere else; running over real code, that
    single rule produced 657 hits in pandas, almost all of them legitimate API
    surface.  Grading the evidence keeps those from drowning the real findings,
    and tells the reader which facts still need a judgement call.
    """

    DEFINITE = "definite"
    """Mechanically certain, and a smell in essentially any context."""

    LIKELY = "likely"
    """Certain as a fact; usually a smell, but a sensible exception exists."""

    CONTEXTUAL = "contextual"
    """Certain as a fact; whether it is a smell depends on intent or hotness."""


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

    strength: Strength = Strength.LIKELY
    detail: dict = field(default_factory=dict)
    """Analyzer-specific facts (loop depth, estimated trip count, ...)."""

    source: str = "ast"
    """Which analyzer family produced this, for the report to cite."""

    def __str__(self) -> str:
        return f"[{self.kind}/{self.strength.value}] line {self.lineno}: {self.message}"
