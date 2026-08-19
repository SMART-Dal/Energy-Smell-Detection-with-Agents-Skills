"""C6.S6 Unmanaged Resource Lifecycle -- when the handle is released, not
whether.

Both variants close every handle, so this isolates the one thing a paired
comparison can see: `before` holds all of them open until the end of the call,
`after` releases each as soon as it is done. The card says the energy cost of
one open handle is small and the cost of exhausting a descriptor table is a
failure mode rather than a slowdown -- so a reading near zero here is the card
being right, and the finding it should report is the descriptor count.
"""

import os
import tempfile
from contextlib import ExitStack

_DIR = tempfile.mkdtemp(prefix="c6s6b-")
_PATHS = []
for _i in range(400):
    _p = os.path.join(_DIR, f"f{_i}.txt")
    with open(_p, "w", encoding="utf-8") as _h:
        _h.write("payload " * 40)
    _PATHS.append(_p)


def before(count):
    total = 0
    with ExitStack() as stack:
        for path in _PATHS[:count]:
            handle = stack.enter_context(open(path, encoding="utf-8"))
            total += len(handle.read())      # every handle stays open until the end
    return total


def after(count):
    total = 0
    for path in _PATHS[:count]:
        with open(path, encoding="utf-8") as handle:
            total += len(handle.read())      # released immediately
    return total


def cases():
    return [("many-handles", lambda: (400,)),
            ("few-handles",  lambda: (5,)),
            ("edge",         lambda: (0,))]
