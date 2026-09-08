"""C6.S7 Mutable Default Arguments -- a mutable default the body never mutates.

The card's second `NOT a smell when` clause: a mutable default that is only
read is not accumulating anything, though it is still fragile. The usual repair
still applies mechanically -- `seen=None` plus a guard -- and it costs a
comparison on every call while saving nothing at all.

Expected to read at or below zero, which is the answer that stops an agent
applying this root cause to every mutable default it sees rather than to the
ones that grow.
"""

_ALLOWED = ("read", "write", "admin")


def _check_shared(scope, allowed=list(_ALLOWED)):
    return scope in allowed                 # read-only: nothing accumulates


def _check_guarded(scope, allowed=None):
    if allowed is None:
        allowed = list(_ALLOWED)
    return scope in allowed


def before(scopes):
    return sum(1 for s in scopes if _check_shared(s))


def after(scopes):
    return sum(1 for s in scopes if _check_guarded(s))


def cases():
    scopes = [("read", "write", "admin", "none")[i % 4] for i in range(400_000)]
    return [("many-calls", lambda: (list(scopes),)),
            ("few-calls",  lambda: (scopes[:40],))]
