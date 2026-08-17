"""One handle per iteration, none of them closed.

The single-handle case is mostly a tidiness argument; this one is a real
resource exhaustion bug, because the loop opens a descriptor per input and the
rebinding of `part` only drops the previous file when the collector notices.
The destination handle is a second, longer-lived leak in the same function, so
the rule has to report both bindings rather than only the first opener it
meets.
"""

from __future__ import annotations


def merge_parts(paths, destination):
    """Concatenate every part file into one destination file."""
    output = open(destination, "w", encoding="utf-8")  # EXPECT
    for path in paths:
        part = open(path, encoding="utf-8")  # EXPECT
        output.write(part.read())
        output.write("\n")
    return destination
