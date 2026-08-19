"""C8.S4 Redundant External Fetching -- the same file read once per row.

The card says an external fetch costs orders of magnitude more than anything
in-process, and that the load-bearing question is how often the source actually
changes. Here it does not change at all during the call, so caching for the
duration is sound -- and the card asks the finding to say that rather than
saying "cache it".
"""

import os
import tempfile

_HANDLE, _PATH = tempfile.mkstemp(suffix=".c8s4")
with os.fdopen(_HANDLE, "w", encoding="utf-8") as _out:
    _out.write("setting=%d\n" % 7 * 1)
    for _i in range(200):
        _out.write(f"key{_i}=value{_i}\n")


def _read_setting():
    with open(_PATH, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("setting="):
                return int(line.split("=", 1)[1])
    return 0


def before(rows):
    total = 0
    for row in rows:
        total += row * _read_setting()
    return total


def after(rows):
    setting = _read_setting()
    total = 0
    for row in rows:
        total += row * setting
    return total


def cases():
    return [("many-rows", lambda: (list(range(4_000)),)),
            ("one-row",   lambda: ([1],)),
            ("edge",      lambda: ([],))]
