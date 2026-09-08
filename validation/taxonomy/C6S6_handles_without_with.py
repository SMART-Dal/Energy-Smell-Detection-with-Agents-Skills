"""C6.S6 Unmanaged Resource Lifecycle -- many handles, none closed on the
failure path.

The card is clear that on CPython the repaired and unrepaired versions usually
close at the same moment, so a paired comparison measures nothing and the claim
is about the failure path and about exhaustion at scale. This file exists to
put a number on "nothing", so the card can say so rather than implying an
energy saving it does not have.
"""

import os
import tempfile

_DIR = tempfile.mkdtemp(prefix="c6s6-")
_PATHS = []
for _i in range(200):
    _p = os.path.join(_DIR, f"f{_i}.txt")
    with open(_p, "w", encoding="utf-8") as _h:
        _h.write("payload " * 50)
    _PATHS.append(_p)


def before(count):
    total = 0
    for path in _PATHS[:count]:
        handle = open(path, encoding="utf-8")     # never closed explicitly
        total += len(handle.read())
    return total


def after(count):
    total = 0
    for path in _PATHS[:count]:
        with open(path, encoding="utf-8") as handle:
            total += len(handle.read())
    return total


def cases():
    return [("many-handles", lambda: (200,)),
            ("few-handles",  lambda: (5,))]
