"""C3.S7 Collection Modification During Iteration -- `del` inside a `while`,
rebuilt instead.

The card is explicit that this is a correctness finding with an energy
consequence, and that a `before` which skips elements is not equivalent to its
repair by construction. So `before` here is the *fixed* incremental version --
it does not increment after deleting, so it visits everything -- and the
measurement isolates the quadratic `del` rather than the bug. The bug is real
and belongs in the report; it is just not what a paired comparison can measure.
"""

def before(values):
    i = 0
    while i < len(values):
        if values[i] is None:
            del values[i]                 # shifts the tail; no increment after
        else:
            i += 1
    return values


def after(values):
    values[:] = [v for v in values if v is not None]
    return values


def _values(n, none_ratio):
    return [None if (i * 7919) % 100 < none_ratio * 100 else i for i in range(n)]


def cases():
    return [("many-removals", lambda: (_values(40_000, 0.5),)),
            ("few-removals",  lambda: (_values(40_000, 0.01),)),
            ("edge",          lambda: ([],))]
