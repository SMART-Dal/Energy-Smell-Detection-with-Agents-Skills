"""C1.S8 Excessive Runtime-Management Calls -- guarding a log
call that has nothing to build.

The repair is real and `C1S8_log_argument` measures it at +93% with the level
off: an f-string that serialises a record is evaluated before `debug()` is
entered, so the work happens whether or not anything is emitted.

The guard is worth what the arguments cost. Here they cost nothing -- a literal
and one integer that already exists -- so `isEnabledFor` adds a method call and
a comparison per record in front of a call whose own first act is the same
comparison in C. The check is done twice and the saving is zero.

Both readings should be at or below zero, which is what stops the guard being
applied to every `logger.debug` in a file.
"""

import logging

_log = logging.getLogger("c1s8-counter")
_log.addHandler(logging.NullHandler())
_log.propagate = False


def before(records, level):
    _log.setLevel(level)
    seen = 0
    for record in records:
        _log.debug("processed record %s", record)     # nothing to pre-compute
        seen += record
    return seen


def after(records, level):
    _log.setLevel(level)
    seen = 0
    for record in records:
        if _log.isEnabledFor(logging.DEBUG):
            _log.debug("processed record %s", record)
        seen += record
    return seen


def cases():
    return [("debug-off", lambda: (list(range(200_000)), logging.WARNING)),
            ("debug-on",  lambda: (list(range(20_000)), logging.DEBUG)),
            ("edge",      lambda: ([], logging.WARNING))]
