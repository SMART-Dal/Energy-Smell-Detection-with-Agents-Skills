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
            "the arguments end up in different states: `before` and `after` "
            "do not mutate their inputs the same way. If that is deliberate "
            "and no call site depends on the mutation, relax equivalence to "
            "`returns_only` and give the reason."
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


# -- comparing two copies of the code ----------------------------------------
#
# A submitted repair runs against two copies of the repository, so its two
# results are instances of two copies of every class and never compare equal
# as live objects. Each side renders what it produced into JSON, and the
# renderings are compared. The rules below exist so that two results the
# in-process check would call equal render the same:
#
#   * memory addresses are stripped, since two objects never share one;
#   * each side's repository copy and scratch directory are replaced by a
#     placeholder, since a result that names a file it wrote names a
#     different directory on each side;
#   * an integral float renders as an int, as `1 == 1.0` is true in-process;
#   * sets and dict items are ordered by their rendering, not by hashing;
#   * an object without `__eq__` renders as its class and attributes, which is
#     the structural comparison `_same` falls back to.
#
# Two renderings exist. The tagged one keeps a list distinct from a tuple and
# is what the default check compares. The plain one is what a submission's own
# `equivalent(before, after)` receives: lists, dicts, numbers and strings.

import base64 as _base64
import json as _json
import math as _math
import re as _re
from pathlib import PurePath as _PurePath

_ADDRESS = _re.compile(r" at 0x[0-9a-fA-F]+")
_MAX_DEPTH = 8


def render(value, *, plain: bool = False, replace: tuple = ()):
    """`value` as JSON-serialisable data, comparable across processes."""
    return _render(value, plain, tuple(replace), 0, set())


def render_json(value, *, plain: bool = False, replace: tuple = ()) -> str:
    """The rendering as one canonical string, so equality is string equality."""
    return _json.dumps(render(value, plain=plain, replace=replace),
                       sort_keys=True, separators=(",", ":"))


def normalise_text(text: str, replace: tuple) -> str:
    """Placeholders for the per-side paths, then no memory addresses."""
    for old, new in replace:
        text = text.replace(old, new)
    return _ADDRESS.sub(" at 0x<ADDR>", text)


def _render(value, plain, replace, depth, seen):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if _math.isnan(value):
            return "nan" if plain else {"float": "nan"}
        if _math.isinf(value):
            text = "inf" if value > 0 else "-inf"
            return text if plain else {"float": text}
        if value.is_integer() and abs(value) < 2 ** 53:
            return int(value)
        return value
    if isinstance(value, complex):
        return [value.real, value.imag] if plain else {"complex": [value.real, value.imag]}
    if isinstance(value, str):
        return normalise_text(value, replace)
    if isinstance(value, (bytes, bytearray)):
        encoded = _base64.b64encode(bytes(value)).decode("ascii")
        return encoded if plain else {type(value).__name__: encoded}
    if isinstance(value, _PurePath):
        text = normalise_text(str(value), replace)
        return text if plain else {"path": text}

    if depth >= _MAX_DEPTH:
        return "<deep>"
    if id(value) in seen:
        return "<cycle>"
    seen = seen | {id(value)}
    deeper = depth + 1

    if isinstance(value, (list, tuple)):
        items = [_render(v, plain, replace, deeper, seen) for v in value]
        return items if plain else {type(value).__name__: items}
    if isinstance(value, (set, frozenset)):
        items = sorted((_render(v, plain, replace, deeper, seen) for v in value),
                       key=lambda v: _json.dumps(v, sort_keys=True))
        return items if plain else {type(value).__name__: items}
    if isinstance(value, dict):
        pairs = sorted(
            ((_render(k, plain, replace, deeper, seen), _render(v, plain, replace, deeper, seen))
             for k, v in value.items()),
            key=lambda kv: _json.dumps(kv[0], sort_keys=True),
        )
        if plain:
            return {k if isinstance(k, str) else _json.dumps(k, sort_keys=True): v
                    for k, v in pairs}
        return {"dict": [list(kv) for kv in pairs]}

    tolist = getattr(value, "tolist", None)
    if callable(tolist) and hasattr(value, "shape"):
        try:
            data = _render(tolist(), plain, replace, deeper, seen)
            return data if plain else {"array": data, "dtype": str(getattr(value, "dtype", ""))}
        except Exception:  # noqa: BLE001
            pass

    attributes = getattr(value, "__dict__", None)
    slots = getattr(type(value), "__slots__", None)
    if attributes is not None or slots:
        fields = dict(attributes or {})
        for name in ([slots] if isinstance(slots, str) else (slots or ())):
            if hasattr(value, name):
                fields[name] = getattr(value, name)
        rendered = {k: _render(v, plain, replace, deeper, seen) for k, v in sorted(fields.items())}
        name = type(value).__qualname__
        if plain:
            return {"__class__": name, **rendered}
        return {"object": name, "attrs": rendered}

    return normalise_text(repr(value), replace)
