"""Does the repair actually preserve behaviour?

Run before an energy measurement, and fatal if it fails. A faster variant that
computes something else is not a repair, and measuring it would produce a
number that looks like a result.

Four observable channels are compared, because a Python function can differ in
all four:

    return value        the obvious one
    argument state      `after` may fail to mutate what `before` mutated
    stdout              printing is behaviour too
    exception           same type, for inputs that are supposed to raise

This is a differential check on the cases the agent supplied, not a proof. It
catches the mistakes that actually happen -- a repair that drops the last
element, that returns a generator where a list was expected, that stops
mutating in place -- and it is deliberately not more than that.
"""

from __future__ import annotations

import copy
import io
import contextlib
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseResult:
    """What happened when one case was run through both variants."""

    label: str
    equivalent: bool
    mutates_args: bool
    """True when `before` changed its arguments -- affects how we measure."""
    difference: str = ""
    """Which channel diverged, and how. Empty when equivalent."""


def check(case_file, case) -> CaseResult:
    """Run one case through both variants and compare every observable."""
    before_args = case.args()
    before_snapshot = _snapshot(before_args)
    before_outcome, before_stdout = _invoke(case_file.before, before_args)
    mutates = not _same(before_snapshot, _snapshot(before_args))

    after_args = case.args()
    after_outcome, after_stdout = _invoke(case_file.after, after_args)

    difference = _compare(
        before=(before_outcome, before_stdout, before_args),
        after=(after_outcome, after_stdout, after_args),
        same_value=_value_comparison(case_file),
        compare_args=getattr(case_file, "equivalence", "strict") == "strict",
    )
    return CaseResult(
        label=case.label,
        equivalent=not difference,
        mutates_args=mutates,
        difference=difference,
    )


def _value_comparison(case_file):
    """The case file's own return-value comparison, or the default one.

    A case file may declare `equivalent(before, after)` when "the same answer"
    is genuinely wider than `==` -- a repair that returns floats where the
    original returned ints, or an unordered result. It has to explain itself in
    a docstring, and the verdict says it was used.
    """
    custom = getattr(case_file, "custom_equivalent", None)
    if custom is None:
        return _same

    def compare(left, right) -> bool:
        return bool(custom(left, right))

    return compare


def _invoke(function, args):
    """Call a variant, capturing its return value or exception, and its stdout."""
    stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(stream):
            return ("return", function(*args)), stream.getvalue()
    except Exception as exc:  # noqa: BLE001 -- raising is a behaviour to compare
        return ("raise", type(exc).__name__), stream.getvalue()


def _compare(*, before, after, same_value=None, compare_args: bool = True) -> str:
    (before_outcome, before_stdout, before_args) = before
    (after_outcome, after_stdout, after_args) = after
    same_value = same_value or _same

    before_kind, before_value = before_outcome
    after_kind, after_value = after_outcome

    if before_kind != after_kind:
        return (
            f"before {_describe(before_kind, before_value)}, "
            f"after {_describe(after_kind, after_value)}"
        )
    if before_kind == "raise":
        if before_value != after_value:
            return f"before raised {before_value}, after raised {after_value}"
        return ""
    if not same_value(before_value, after_value):
        return (
            f"different return value: before -> {_short(before_value)}, "
            f"after -> {_short(after_value)}"
        )
    if compare_args and not _same(_snapshot(before_args), _snapshot(after_args)):
        return (
            "the arguments end up in different states: `before` and `after` do "
            "not mutate their inputs the same way. If that is deliberate and "
            "the call sites do not depend on it, say so with "
            "`EQUIVALENCE = \"returns_only\"`."
        )
    if before_stdout != after_stdout:
        return f"different stdout: {_short(before_stdout)} vs {_short(after_stdout)}"
    return ""


def _snapshot(args: tuple):
    """A copy of the arguments, so mutation during the call stays visible.

    Falls back to `repr` for anything that will not deep-copy (file handles,
    locks, live connections). Comparing reprs is weaker, but an argument that
    cannot be copied is one this check cannot say much about anyway.
    """
    try:
        return copy.deepcopy(args)
    except Exception:  # noqa: BLE001
        return repr(args)


def _same(left, right) -> bool:
    """Equality that survives numpy arrays, plain objects and odd __eq__.

    Three cases have to work, and the naive `left == right` gets two wrong:

        [1, 2, 3]        `==` is meaningful               -> use it
        np.array(...)    `==` returns an array            -> reduce with .all()
        AB()             `==` is identity                 -> compare structure

    The third is the one that bites. A class that defines no `__eq__` compares
    by identity, so a snapshot taken with deepcopy never equals the original and
    every argument holding such an object looks mutated. Falling back to `repr`
    does not help either: the default repr embeds the memory address, which the
    copy also changes.

    A `False` from `==` is therefore never trusted on its own -- it is checked
    against the structural comparison before being believed. Identity semantics
    hide one level down as readily as at the top: `[AB(1)] == [AB(1)]` is False
    for the same reason `AB(1) == AB(1)` is.
    """
    try:
        result = left == right
    except Exception:  # noqa: BLE001
        return _structure(left) == _structure(right)

    if isinstance(result, bool):
        return result or _structure(left) == _structure(right)

    reduce_all = getattr(result, "all", None)
    if callable(reduce_all):
        try:
            return bool(reduce_all())
        except Exception:  # noqa: BLE001
            pass
    try:
        return bool(result)
    except Exception:  # noqa: BLE001
        return _structure(left) == _structure(right)


def _structure(value, depth: int = 0):
    """An address-free, comparable rendering of a value and what it contains.

    Recurses through containers and object attributes so that two structurally
    identical objects compare equal even when neither defines `__eq__`. Bounded
    depth, because argument graphs in real code contain cycles and a case file
    is allowed to pass one in.
    """
    if depth > 6:
        return "<deep>"
    if isinstance(value, (int, float, complex, str, bytes, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, [_structure(v, depth + 1) for v in value])
    if isinstance(value, (set, frozenset)):
        return (type(value).__name__, sorted(repr(v) for v in value))
    if isinstance(value, dict):
        return ("dict", sorted((repr(k), _structure(v, depth + 1)) for k, v in value.items()))

    attributes = getattr(value, "__dict__", None)
    if attributes is not None:
        return (
            type(value).__name__,
            sorted((k, _structure(v, depth + 1)) for k, v in attributes.items()),
        )
    slots = getattr(type(value), "__slots__", None)
    if slots:
        return (
            type(value).__name__,
            [(s, _structure(getattr(value, s, None), depth + 1)) for s in slots],
        )
    return repr(value)


def _describe(kind: str, value) -> str:
    return f"raised {value}" if kind == "raise" else f"returned {_short(value)}"


def _short(value, limit: int = 120) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "..."
