"""C9.S1 Fragmented I/O Calls -- many small writes against one batched write."""

import os, tempfile

_DIR = tempfile.mkdtemp()


def before(lines):
    path = os.path.join(_DIR, "a.txt")
    with open(path, "w") as f:
        for line in lines:
            f.write(line)
            f.flush()
    return os.path.getsize(path)


def after(lines):
    path = os.path.join(_DIR, "b.txt")
    with open(path, "w") as f:
        f.write("".join(lines))
    return os.path.getsize(path)


def cases():
    return [("many-lines", lambda: ([f"line {i}\n" for i in range(20_000)],)),
            ("few-lines", lambda: ([f"line {i}\n" for i in range(5)],))]
