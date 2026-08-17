"""Handles whose lifetime deliberately outlives this function.

Nothing here closes anything, and none of it is a leak: the handle is given to
someone else, and that someone else closes it.  A rule that only asked "is
there a `with`?" would report every one of these, and they are all ordinary
code -- a factory that opens and returns, a class that owns a connection for its
lifetime, an `ExitStack` collecting handles whose count is not known until run
time, and a generator that hands the reader to its consumer.

This is the exemption that matters most in practice, because it is what library
code looks like.  The boundary is `_passes_on`: giving the handle away is fine,
and `return handle.read()` is not giving it away -- that keeps the contents and
abandons the handle, so it still reports.
"""

from __future__ import annotations

from contextlib import ExitStack


def open_log(path):
    """Open the log and let the caller decide when it closes."""
    handle = open(path, "a", encoding="utf-8")
    handle.write("--- session start\n")
    return handle


class Store:
    """Owns its connection for as long as the store exists."""

    def connect(self, dsn, driver):
        connection = driver.connect(dsn)
        self._connection = connection
        return connection


def merge_all(paths, destination):
    """Open a variable number of inputs; the stack closes every one of them."""
    with ExitStack() as stack:
        writer = open(destination, "w", encoding="utf-8")
        stack.enter_context(writer)
        for path in paths:
            reader = open(path, encoding="utf-8")
            stack.enter_context(reader)
            writer.write(reader.read())
    return destination


def stream_rows(path):
    """Yield the reader itself, so the consumer's `with` manages it."""
    handle = open(path, encoding="utf-8")
    yield handle
