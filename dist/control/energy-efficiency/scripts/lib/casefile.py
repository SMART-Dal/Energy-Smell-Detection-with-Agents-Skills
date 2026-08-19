"""Loading and validating a case file.

A case file is the whole interface between the agent and the verifier:

    before(*args)   the pattern as it appears in the repository
    after(*args)    the canonical repair, and no other change
    cases()         [(label, thunk)] -- thunk returns a fresh args tuple

Thunks rather than values, because `before` may mutate its arguments. Every
repetition gets a fresh input, built outside the measured window, so one
sample cannot poison the next.

Two optional declarations relax the equivalence check, for the cases where
"identical" is stricter than "the same answer":

    EQUIVALENCE = "returns_only"   ignore how the arguments end up
    def equivalent(before, after)  compare return values your own way

Both are opt-in, both must carry a reason, and both are reported in the verdict
so that nobody can quietly weaken the check and call the result confirmed. See
`RELAXATIONS` for what each one is honestly for, and what it is not.

Validation is strict and the messages say what to fix. A malformed case file is
the most likely thing to go wrong in the whole pipeline: it is the one artefact
written from scratch each time, by a model, under no schema.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable

RELAXATIONS = {
    "strict": "",
    "returns_only": (
        "argument state is not compared: `before` and `after` may leave their "
        "inputs differently, as long as they return the same answer"
    ),
}
"""Legal values of `EQUIVALENCE`, and what each one stops checking.

`returns_only` exists because a real refactoring sometimes trades a mutation
for an allocation -- `lst.sort()` against `sorted(lst)`, `a.extend(b)` against
`a + b`. Both compute the same answer; only one disturbs the caller's data.
Whether that difference matters is a property of the call sites, which the
verifier cannot see and the agent can, so it is the agent's call to make and
the agent's claim to defend.

It is not a way to make a broken repair pass. A repair that returns a set where
the original returned a list, or that is off by one, still fails: the return
value is compared either way.
"""


class CaseFileError(ValueError):
    """The case file does not meet the contract. The message says how."""


@dataclass(frozen=True)
class Case:
    """One named input to the pair of variants."""

    label: str
    make_args: Callable[[], tuple]

    def args(self) -> tuple:
        """A fresh argument tuple. Called outside every measured window."""
        produced = self.make_args()
        if not isinstance(produced, tuple):
            raise CaseFileError(
                f"case {self.label!r}: the thunk returned "
                f"{type(produced).__name__}, expected a tuple of arguments. "
                f"A single argument still needs a trailing comma: `lambda: (xs,)`"
            )
        return produced


@dataclass(frozen=True)
class CaseFile:
    """A loaded case file: two variants and the inputs to run them on."""

    path: Path
    module: ModuleType
    cases: tuple[Case, ...]
    equivalence: str = "strict"
    """Which comparison this file asked for. See `RELAXATIONS`."""

    @property
    def before(self) -> Callable:
        return self.module.before

    @property
    def after(self) -> Callable:
        return self.module.after

    @property
    def custom_equivalent(self) -> Callable | None:
        """The file's own return-value comparison, if it declared one."""
        return getattr(self.module, "equivalent", None)

    @property
    def relaxations(self) -> tuple[str, ...]:
        """Every weakening of the default check, in words, for the report."""
        notes = []
        if RELAXATIONS.get(self.equivalence):
            notes.append(RELAXATIONS[self.equivalence])
        if self.custom_equivalent is not None:
            reason = (self.custom_equivalent.__doc__ or "").strip().splitlines()
            notes.append(
                "return values compared by the case file's own `equivalent()`"
                + (f": {reason[0]}" if reason else "")
            )
        return tuple(notes)

    def variant(self, name: str) -> Callable:
        return getattr(self.module, name)


def load_case_file(path: Path) -> CaseFile:
    """Import a case file and check it against the contract."""
    path = path.resolve()
    if not path.exists():
        raise CaseFileError(f"no such case file: {path}")

    module = _import(path)

    missing = [name for name in ("before", "after", "cases") if not hasattr(module, name)]
    if missing:
        raise CaseFileError(
            f"{path.name} is missing {', '.join(missing)}. A case file needs "
            f"`before(*args)`, `after(*args)` and `cases()`."
        )
    for name in ("before", "after", "cases"):
        if not callable(getattr(module, name)):
            raise CaseFileError(f"{path.name}: `{name}` must be a function.")

    equivalence = getattr(module, "EQUIVALENCE", "strict")
    if equivalence not in RELAXATIONS:
        raise CaseFileError(
            f"{path.name}: EQUIVALENCE = {equivalence!r} is not one of "
            f"{sorted(RELAXATIONS)}."
        )
    custom = getattr(module, "equivalent", None)
    if custom is not None:
        if not callable(custom):
            raise CaseFileError(f"{path.name}: `equivalent` must be a function.")
        if not (custom.__doc__ or "").strip():
            raise CaseFileError(
                f"{path.name}: `equivalent()` needs a docstring saying why the "
                f"default comparison is too strict for this repair. Relaxing the "
                f"check without a stated reason is how a broken repair gets "
                f"reported as confirmed."
            )

    return CaseFile(
        path=path,
        module=module,
        cases=_read_cases(module, path),
        equivalence=equivalence,
    )


def _read_cases(module: ModuleType, path: Path) -> tuple[Case, ...]:
    raw = module.cases()
    try:
        entries = list(raw)
    except TypeError:
        raise CaseFileError(
            f"{path.name}: cases() returned {type(raw).__name__}, expected a list."
        ) from None

    if not entries:
        raise CaseFileError(
            f"{path.name}: cases() returned nothing. Give at least a large case; "
            f"an edge case and a small case as well is better."
        )

    cases = []
    seen = set()
    for position, entry in enumerate(entries):
        if not (isinstance(entry, (tuple, list)) and len(entry) == 2):
            raise CaseFileError(
                f"{path.name}: case {position} is not a (label, thunk) pair."
            )
        label, thunk = entry
        if not isinstance(label, str) or not label:
            raise CaseFileError(f"{path.name}: case {position} has no label.")
        if not callable(thunk):
            raise CaseFileError(
                f"{path.name}: case {label!r} gives a value where a thunk was "
                f"expected. Write `lambda: (xs,)`, not `(xs,)` -- the thunk is "
                f"called again for every repetition so that a mutating variant "
                f"cannot poison the next sample."
            )
        if label in seen:
            raise CaseFileError(f"{path.name}: duplicate case label {label!r}.")
        seen.add(label)
        cases.append(Case(label=label, make_args=thunk))
    return tuple(cases)


def _import(path: Path) -> ModuleType:
    """Import a file by path, under a name that cannot collide with anything.

    The module is registered in `sys.modules` before it executes, which matters
    for one specific and otherwise baffling failure: `multiprocessing` pickles a
    worker function *by name*, so a case file that hands one to a
    `ProcessPoolExecutor` gets `Can't pickle <function ...>: import of module
    failed` unless the name resolves. That blocked exactly the repair some cards
    recommend for CPU-bound work, and the error names neither the case file nor
    the pool.

    Registering before `exec_module` rather than after is deliberate: a module
    that fails halfway is removed again below, and a module that imports itself
    would otherwise recurse.
    """
    name = f"_case_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CaseFileError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 -- the agent needs the real reason
        del sys.modules[name]
        raise CaseFileError(f"{path.name} failed to import: {exc!r}") from exc
    return module
