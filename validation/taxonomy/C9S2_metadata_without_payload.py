"""C9.S2 Over-Fetching Data -- asking the source for a property, not the payload.

The largest ratio in this root cause: the original transfers every byte of a
file in order to measure it, where the filesystem already knows the answer.
`os.path.getsize` is one `stat`; `open().read()` is an open, a full transfer
and an allocation of the whole content.

The other measured files in this root cause narrow what is fetched -- fewer
columns, fewer rows. This one fetches nothing at all, which is what "can the
source answer the question itself" is asking.
"""

import os
import tempfile

_DIR = tempfile.mkdtemp(prefix="c9s2-")


def _fixture(count, size):
    paths = []
    for i in range(count):
        path = os.path.join(_DIR, f"f{size}-{i}.bin")
        if not os.path.exists(path):
            with open(path, "wb") as handle:
                handle.write(b"x" * size)
        paths.append(path)
    return paths


_BIG = _fixture(40, 400_000)
_SMALL = _fixture(40, 64)


def before(paths):
    total = 0
    for path in paths:
        with open(path, "rb") as handle:
            total += len(handle.read())
    return total


def after(paths):
    total = 0
    for path in paths:
        total += os.path.getsize(path)
    return total


def cases():
    return [("large-payloads", lambda: (list(_BIG),)),
            ("small-payloads", lambda: (list(_SMALL),))]
