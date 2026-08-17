"""A file opened, read and abandoned: the shape the rule is named after.

Nothing closes the handle and nothing else can: it is bound to a local, the
local never leaves the function, and the function returns the parsed contents
rather than the file.  On CPython the refcount drops at the return and the file
closes almost immediately, which is exactly why this survives review -- on
PyPy, or once the function grows an early `return`, it does not.
"""

from __future__ import annotations

import json


def load_config(path):
    """Read a JSON config from disk."""
    handle = open(path, encoding="utf-8")  # EXPECT
    text = handle.read()
    return json.loads(text)


def write_report(path, rows):
    """Write one row per line."""
    out = open(path, "w", encoding="utf-8")  # EXPECT
    for row in rows:
        out.write(f"{row}\n")
    return path
