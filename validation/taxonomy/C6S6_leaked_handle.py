"""C6.S6 Leaked Resource Handles -- open() without a context manager."""

import tempfile, os


def before(paths):
    total = 0
    for p in paths:
        f = open(p)
        total += len(f.read())
        f.close()
    return total


def after(paths):
    total = 0
    for p in paths:
        with open(p) as f:
            total += len(f.read())
    return total


def _make():
    d = tempfile.mkdtemp()
    paths = []
    for i in range(200):
        p = os.path.join(d, f"f{i}.txt")
        with open(p, "w") as f:
            f.write("x" * 256)
        paths.append(p)
    return paths


_PATHS = _make()


def cases():
    return [("many-files", lambda: (list(_PATHS),))]
