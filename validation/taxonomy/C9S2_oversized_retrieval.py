"""C9.S2 Oversized Data Retrieval -- reading a whole file to use its first lines."""

import os, tempfile

_FD, _PATH = tempfile.mkstemp(suffix=".txt")
with open(_PATH, "w") as _f:
    for _i in range(200_000):
        _f.write(f"row {_i}\n")
os.close(_FD)


def before(n):
    with open(_PATH) as f:
        rows = f.read().splitlines()
    return len(rows[:n])


def after(n):
    out = []
    with open(_PATH) as f:
        for line in f:
            out.append(line.rstrip("\n"))
            if len(out) >= n:
                break
    return len(out)


def cases():
    return [("needs-few", lambda: (10,)), ("needs-all", lambda: (200_000,))]
