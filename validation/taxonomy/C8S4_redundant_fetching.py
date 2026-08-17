"""C8.S4 Redundant Data Fetching -- the same file re-read per iteration.

Stands in for a network fetch: the point is a repeated external read whose
answer does not change.
"""

import os, tempfile

_FD, _PATH = tempfile.mkstemp(suffix=".txt")
with open(_PATH, "w") as _f:
    _f.write("x" * 8192)
os.close(_FD)


def before(keys):
    total = 0
    for _ in keys:
        with open(_PATH) as f:
            total += len(f.read())
    return total


def after(keys):
    with open(_PATH) as f:
        content = f.read()
    return sum(len(content) for _ in keys)


def cases():
    return [("many-reads", lambda: (list(range(2_000)),)),
            ("one-read", lambda: ([1],))]
