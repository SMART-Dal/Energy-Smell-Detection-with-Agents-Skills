"""Handles closed on purpose, without a `with` in the header.

A `with` is the idiom, but it is not the only way to close a file at a
determined moment, and the rule is about *whether* the handle is released --
not about which syntax released it.  Three shapes here:

`try`/`finally` is what you have to write when the acquisition and the release
sit either side of code that may raise but must not abort the release; a plain
`.close()` on a straight-line path is enough when nothing between the two can
raise; and adopting an already-open handle with a later `with` is the shape
numpy writes in four separate modules, which is how this exemption was found.
"""

from __future__ import annotations

import json
from contextlib import closing


def load_config(path):
    """Read a JSON config, releasing the handle even if parsing raises."""
    handle = open(path, encoding="utf-8")
    try:
        return json.load(handle)
    finally:
        handle.close()


def line_count(path):
    """Count lines, closing before returning."""
    handle = open(path, encoding="utf-8")
    total = sum(1 for _ in handle)
    handle.close()
    return total


def fetch_rows(connect, query):
    """Open a cursor now, hand it to a `with` on a later line."""
    cursor = connect().cursor()
    with closing(cursor):
        cursor.execute(query)
        return cursor.fetchall()
