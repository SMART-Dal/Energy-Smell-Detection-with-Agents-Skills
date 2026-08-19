"""C6.S3 Unnecessary Data Materialization -- reading a whole file to walk it
once.

The card calls this its clearest case, because the eager alternative is bounded
only by the file. `small-file` is where the whole thing fits comfortably and
the streaming form can only cost its per-line resumption, which is the trade
the card asks the reader to weigh.
"""

import os
import tempfile


def _fixture(lines):
    handle, path = tempfile.mkstemp(suffix=".c6s3")
    with os.fdopen(handle, "w", encoding="utf-8") as out:
        for i in range(lines):
            out.write(f"line {i} with some padding text\n")
    return path


_BIG = _fixture(300_000)
_SMALL = _fixture(50)


def before(path):
    with open(path, encoding="utf-8") as handle:
        return sum(len(line) for line in handle.read().splitlines())


def after(path):
    with open(path, encoding="utf-8") as handle:
        return sum(len(line.rstrip("\n")) for line in handle)


def cases():
    return [("big-file",   lambda: (_BIG,)),
            ("small-file", lambda: (_SMALL,)),
            ("edge",       lambda: (_SMALL,))]
