"""C6.S6 Leaked Resource Handles -- LOOKS THE SAME, IS NOT: the handle is the return
value.

"Always use context managers to ensure deterministic cleanup" is the
description, and `C6S6_prompt_release` measures what prompt release is worth.
Wrapping an `open()` in a `with` is close to a reflex.

The handle here is returned. Wrapping the `open()` closes it at the end of the
function, so the caller gets a closed file and the first read raises
`ValueError: I/O operation on closed file`. The resource is not leaking; its
lifetime is longer than the function that creates it, which is what a factory
does.

Before adding a `with`, find where the handle goes. A handle that is returned,
stored on an instance, put in a pool or yielded from a generator belongs to
something else -- the fix there is a context manager on the *caller*, or a
`close()` on the owner, not a `with` around the open.
"""

import os
import tempfile

_DIR = tempfile.mkdtemp(prefix="c6s6-counter-")
_PATHS = []
for _i in range(200):
    _p = os.path.join(_DIR, f"f{_i}.txt")
    with open(_p, "w", encoding="utf-8") as _h:
        _h.write("payload " * 40)
    _PATHS.append(_p)


def _open_leaky(path):
    return open(path, encoding="utf-8")


def _open_managed(path):
    with open(path, encoding="utf-8") as handle:
        return handle                       # closed before the caller sees it


def before(count):
    total = 0
    for path in _PATHS[:count]:
        handle = _open_leaky(path)
        total += len(handle.read())
        handle.close()
    return total


def after(count):
    total = 0
    for path in _PATHS[:count]:
        handle = _open_managed(path)
        total += len(handle.read())
        handle.close()
    return total


def cases():
    return [("many-handles", lambda: (200,)),
            ("few-handles",  lambda: (5,)),
            ("edge",         lambda: (0,))]
