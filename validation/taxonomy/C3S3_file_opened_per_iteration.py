"""C3.S3 Per-Iteration Object Creation -- a file opened once per row.

The card says resources are worth far more than allocations here: one open and
one close instead of N of each, and the buffer flushed when it fills rather
than on every row. It also names what changes -- a crash mid-loop now loses
buffered rows -- which is a real trade the finding has to state.
"""

import os
import tempfile


def before(rows):
    handle, path = tempfile.mkstemp(suffix=".c3s3")
    os.close(handle)
    try:
        for row in rows:
            with open(path, "a", encoding="utf-8") as out:
                out.write(f"{row}\n")
        return os.path.getsize(path)
    finally:
        os.unlink(path)


def after(rows):
    handle, path = tempfile.mkstemp(suffix=".c3s3")
    os.close(handle)
    try:
        with open(path, "a", encoding="utf-8") as out:
            for row in rows:
                out.write(f"{row}\n")
        return os.path.getsize(path)
    finally:
        os.unlink(path)


def cases():
    return [("many-rows", lambda: (list(range(20_000)),)),
            ("few-rows",  lambda: (list(range(20)),))]
