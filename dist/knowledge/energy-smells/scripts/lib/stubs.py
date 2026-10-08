"""Standing in for a third-party package the host does not have installed.

Whoever runs this works in the environment the target repository already builds
in, so normally nothing here is used. Where that is not true, a module the unit
never touches can still block the import that reaches it: a function needing
only `struct` can sit inside a package whose `__init__` imports a web
framework. Rather than abandon the repository, the missing top-level package is
satisfied by a stub and the import retried.

Two rules keep this honest. The repository's own modules are never stubbed, so
a failure in the code under test still surfaces. And a stub that is *used while
the unit runs* raises, so a repair that genuinely needs the library is refused
rather than measured against a fake -- while a stub merely touched at import
time passes through, because reaching the unit at all means executing the
module scaffolding around it.
"""

from __future__ import annotations

import contextlib
import importlib
import importlib.abc
import importlib.util
import sys
import types
from pathlib import Path


class StubUsed(RuntimeError):
    """A stubbed third-party name was used while the unit was running."""


# A stub is called in two very different situations, and only one is a problem.
# Reaching the unit at all means executing its module, and a module decorates
# its functions, builds registries and subclasses base classes as it loads --
# all of it library scaffolding we have to tolerate or we never get there.
# Once the module is loaded, a call means the unit itself depends on the real
# library, and a number measured against a fake is worthless. So import-time
# calls pass through and run-time calls raise.
_IMPORTING = False


class _StubMeta(type):
    """Attribute access yields another stub; using one raises."""

    def __getattr__(cls, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)          # leave protocol lookups alone
        if not _IMPORTING:
            raise StubUsed(
                f"{cls._path}.{name} was read while the unit ran, so it needs "
                "the real library; measuring it against a stub means nothing"
            )
        return _stub(f"{cls._path}.{name}")

    def __call__(cls, *args, **kwargs):
        if not _IMPORTING:
            raise StubUsed(
                f"{cls._path} was called while the unit ran, so it needs the "
                "real library; measuring it against a stub would mean nothing"
            )
        # The overwhelmingly common import-time call is a decorator, so hand
        # back the decorated object unchanged and leave the module intact.
        if len(args) == 1 and not kwargs and callable(args[0]):
            return args[0]
        return cls

    # Subscription and `|` are how a module writes a type alias at import
    # time -- `ConfigEntry[Coordinator]`, `Device | None`. They describe a
    # type rather than compute anything, so they yield the stub again. Calling
    # one is different: that is the library actually doing work.
    def __getitem__(cls, item):
        return cls

    def __or__(cls, other):
        return cls

    def __ror__(cls, other):
        return cls

    def __repr__(cls):
        return f"<stub {cls._path}>"


def _stub(path: str):
    """A stub is a class, so the repository may still subclass it."""
    return _StubMeta(path.rsplit(".", 1)[-1], (), {"_path": path})


def _module_attr(path: str, name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    if not _IMPORTING:
        raise StubUsed(
            f"{path}.{name} was read while the unit ran, so it needs the real "
            "library; measuring it against a stub means nothing"
        )
    return _stub(f"{path}.{name}")


class _StubLoader(importlib.abc.Loader):
    def create_module(self, spec):
        module = types.ModuleType(spec.name)
        module.__path__ = []                    # every submodule is stubbable too
        module.__getattr__ = lambda name, _p=spec.name: _module_attr(_p, name)
        return module

    def exec_module(self, module):
        return None


class _StubFinder(importlib.abc.MetaPathFinder):
    """Satisfies imports of named top-level packages that are not installed."""

    def __init__(self):
        self.roots: set[str] = set()

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self.roots:
            return importlib.util.spec_from_loader(fullname, _StubLoader())
        return None


@contextlib.contextmanager
def importing():
    """Treat what runs inside as import-time scaffolding.

    For module-level code that is not the unit's own module but still has to
    load -- the inputs' factory importing a sibling module, say. Anything that
    happens later, while the unit runs, is still refused.
    """
    global _IMPORTING
    previous, _IMPORTING = _IMPORTING, True
    try:
        yield
    finally:
        _IMPORTING = previous


def _is_repo_module(root: Path, name: str) -> bool:
    """Is this name part of the repository under test rather than a dependency?"""
    top = name.split(".")[0]
    return (root / top).is_dir() or (root / f"{top}.py").is_file()


def import_with_stubs(root: Path, name: str, limit: int = 20):
    """Import `name`, standing in for uninstalled third-party packages.

    A dependency-free function can sit behind a package whose `__init__`
    imports something heavy -- `protocol/cobs.py` needs only `struct`, but
    reaching it executes an `__init__` that imports Home Assistant. Rather
    than give up on the whole repository, the missing top-level package is
    satisfied by a stub and the import retried.

    The repository's own modules are never stubbed: a failure there is a real
    problem and must surface. Nor is the stub silent -- the names stood in for
    are reported, and any attempt to *use* one raises `StubUsed`, so a unit
    that genuinely depends on the library is refused instead of measured.
    """
    global _IMPORTING
    finder = _StubFinder()
    sys.meta_path.append(finder)                # after the real finders
    stubbed: list[str] = []
    for _ in range(limit):
        try:
            _IMPORTING = True
            return importlib.import_module(name), sorted(stubbed)
        except ModuleNotFoundError as exc:
            missing = exc.name
            if not missing or _is_repo_module(root, missing):
                raise
            top = missing.split(".")[0]
            if top in finder.roots:
                raise                           # stubbing it did not help
            finder.roots.add(top)
            stubbed.append(top)
        finally:
            _IMPORTING = False
    raise ImportError(f"still unresolved after stubbing {stubbed}")
