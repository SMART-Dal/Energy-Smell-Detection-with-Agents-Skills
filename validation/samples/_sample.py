"""Turns one of Javad's hand-written sample pairs into a verifier case file.

`data/manual_sampling/<Category>/<Name>/` holds two files that are already
almost exactly what the verifier wants:

    name.py               a function, then a driver that calls it at scale
    name_refactored.py    the same function, rewritten

88 of the 92 pairs have the identical shape, so the conversion is mechanical:

    import random                    <- prelude: kept, exec'd once per variant
    def sum_top_k(lst, k): ...       <- prelude

    lst = [random.randint(...) ...]  <- setup: kept, exec'd once, args cached
    for _ in range(6):               <- driver: DROPPED, the verifier sizes runs
        a = sum_top_k(lst, 100)         itself, so a hardcoded rep count would
                                        only fight it

From the driver we learn two things we cannot get anywhere else: which function
is the one under test (`sum_top_k`), and what arguments it is meant to be
called with (`lst, 100`).  Everything else is thrown away.

The point of running these is not to grade Javad's samples.  It is that 92
before/after pairs written by a human who was *trying* to save energy are the
closest thing we have to a labelled corpus, and every one that measures as no
better -- or worse -- is a place where a plausible-sounding rule is wrong.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path

SAMPLES_ROOT = Path(__file__).resolve().parents[2] / "data" / "manual_sampling"

PRELUDE_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)

# Types that cannot be mutated by a call, so the thunk can hand out the same
# object every time instead of paying for a deep copy of a million-element list.
IMMUTABLE = (int, float, complex, str, bytes, bool, type(None), tuple, frozenset)


class SampleError(RuntimeError):
    """This pair does not fit the mechanical conversion; convert it by hand."""


# -- taking the sample apart -----------------------------------------------


def _split(source: str) -> tuple[list[ast.stmt], list[ast.stmt], ast.For]:
    """Separate a sample file into prelude, setup and driver loop.

    The driver is the last top-level statement, and it is always a `for` loop
    whose body calls the function under test.  Four of the 92 samples end in
    something else (a bare call, an `if __name__` guard); those raise, and are
    listed as unconvertible rather than silently mis-measured.
    """
    body = ast.parse(source).body
    if not body or not isinstance(body[-1], ast.For):
        raise SampleError("the file does not end in a driver `for` loop")

    driver = body[-1]
    prelude = [node for node in body[:-1] if isinstance(node, PRELUDE_NODES)]
    setup = [node for node in body[:-1] if not isinstance(node, PRELUDE_NODES)]
    return prelude, setup, driver


def _call_in(driver: ast.For, defined: set[str]) -> ast.Call:
    """Find the call to the function under test inside the driver loop.

    A driver body can contain more than one call -- `u.print_name()` and
    `u.change_name(...)` in the ObjectOriented samples -- so we take the first
    call to a name the file itself defines, which is the entry point the sample
    is about.
    """
    for node in ast.walk(driver):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in defined:
                return node
    raise SampleError("the driver loop calls no function this file defines")


def _defined_names(prelude: list[ast.stmt]) -> set[str]:
    return {
        node.name
        for node in prelude
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


# -- putting a case file back together -------------------------------------


def _namespace(prelude: list[ast.stmt], origin: str) -> dict:
    """Execute a sample's imports, functions and classes, and nothing else."""
    module = ast.Module(body=prelude, type_ignores=[])
    namespace: dict = {"__name__": f"_sample_{origin}"}
    exec(compile(ast.fix_missing_locations(module), origin, "exec"), namespace)
    return namespace


def _share_unchanged(before_ns: dict, before_prelude, after_ns: dict, after_prelude) -> None:
    """Make both variants use one definition of everything they did not change.

    Both files carry a full copy of any helper class, so executing them
    separately produces two distinct classes with the same name:

        # add_on_specific_type.py              # ..._refactored.py
        class AB: ...                          class AB: ...        <- a *different* class
        if type(a) == AB                       if isinstance(a, AB)

    The inputs are built from the original's `AB`, so the refactored variant's
    `isinstance` check sees a foreign class and answers False for everything.
    The two functions then disagree and the pair is reported as not equivalent
    -- an artefact of how they were loaded, not of what they do.

    Any top-level definition whose source is byte-identical in both files is
    therefore taken from the original namespace, so shared scaffolding really is
    shared and only the rewritten function differs.
    """
    before_sources = {
        node.name: ast.dump(node)
        for node in before_prelude
        if hasattr(node, "name")
    }
    for node in after_prelude:
        name = getattr(node, "name", None)
        if name and before_sources.get(name) == ast.dump(node):
            after_ns[name] = before_ns[name]


def _build_args(namespace: dict, setup, call, origin: str) -> tuple:
    """Run the sample's own setup and evaluate the call's arguments.

    Takes the *original* variant's live namespace rather than making a fresh
    one. A sample that defines `class AB` and then builds `[AB(i) for i in ...]`
    must populate that list with the very class `before` closes over, or
    `type(a) == AB` is False for every element and the function under test never
    does the work the sample was written to measure.
    """
    exec(
        compile(ast.fix_missing_locations(ast.Module(body=setup, type_ignores=[])), origin, "exec"),
        namespace,
    )
    arguments = ast.Expression(body=ast.Tuple(elts=list(call.args), ctx=ast.Load()))
    return eval(compile(ast.fix_missing_locations(arguments), origin, "eval"), namespace)


def build(category: str, name: str):
    """Return `(before, after, cases)` for one sample pair.

    Used from a generated case file as:

        before, after, cases = build("BuiltInBehavior", "SumTopK")
    """
    directory = SAMPLES_ROOT / category / name
    originals = sorted(p for p in directory.glob("*.py") if not p.stem.endswith("_refactored"))
    refactored = sorted(directory.glob("*_refactored.py"))
    if not originals or not refactored:
        raise SampleError(f"{category}/{name}: expected one file and one _refactored file")

    original_source = originals[0].read_text()
    refactored_source = refactored[0].read_text()

    prelude, setup, driver = _split(original_source)
    function_name = _call_in(driver, _defined_names(prelude)).func.id

    before_namespace = _namespace(prelude, str(originals[0]))
    after_prelude, _, _ = _split(refactored_source)
    after_namespace = _namespace(after_prelude, str(refactored[0]))
    _share_unchanged(before_namespace, prelude, after_namespace, after_prelude)

    if function_name not in after_namespace:
        raise SampleError(
            f"{category}/{name}: the refactored file defines no `{function_name}`"
        )

    call = _call_in(driver, _defined_names(prelude))
    base_args = _build_args(before_namespace, setup, call, str(originals[0]))

    def cases():
        # One case, at the size the sample's own author chose.  Their driver
        # repeated it; the verifier decides repetition itself, so the size is
        # all we keep.
        return [(f"{name}@authored", lambda: _fresh(base_args))]

    return before_namespace[function_name], after_namespace[function_name], cases


def _fresh(args: tuple) -> tuple:
    """A copy of the arguments, skipping the copy where it cannot matter.

    Several samples mutate their input -- `sum_top_k` calls `lst.sort()` -- and
    a sorted list is a different benchmark from an unsorted one.  Handing out
    the same object twice would measure the second call against work the first
    one already did.
    """
    return tuple(a if isinstance(a, IMMUTABLE) else copy.deepcopy(a) for a in args)
