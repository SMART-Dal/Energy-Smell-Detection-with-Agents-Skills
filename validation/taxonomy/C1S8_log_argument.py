"""C1.S8 Excessive Runtime-Management Calls -- an expensive log argument built
whether or not the level is enabled.

The card's second repair example, and the quieter half of this root cause: the
arguments to a log call are evaluated before the logger decides anything, so in
production -- where DEBUG is off -- every record is serialised and thrown away.
Both changes are needed and this pair makes both: the guard, and the deferred
`%s` formatting.

`debug-on` is the adversarial case: with the level enabled the repair can only
cost, since the formatting happens either way.
"""

import json
import logging

_log = logging.getLogger("c1s8")
_log.addHandler(logging.NullHandler())
_log.propagate = False


def before(records, level):
    _log.setLevel(level)
    seen = 0
    for record in records:
        _log.debug(f"record: {json.dumps(record)}")
        seen += record["id"]
    return seen


def after(records, level):
    _log.setLevel(level)
    seen = 0
    for record in records:
        if _log.isEnabledFor(logging.DEBUG):
            _log.debug("record: %s", json.dumps(record))
        seen += record["id"]
    return seen


def _records(n):
    return [{"id": i, "name": f"n{i}", "tags": [1, 2, 3]} for i in range(n)]


def cases():
    return [("debug-off", lambda: (_records(20_000), logging.WARNING)),
            ("debug-on",  lambda: (_records(20_000), logging.DEBUG)),
            ("edge",      lambda: ([], logging.WARNING))]
