"""C4.S5 Expensive Comparison -- genuinely mixed input, where the check is the
algorithm.

The card's first `NOT a smell when` clause, measured. Neither repair is
available: the branches do different things and the elements do not share an
interface, so the only edit left is swapping `isinstance` for `type(x) is`,
which changes behaviour for subclasses. The expected reading is a small loss or
nothing, and either says the same thing.
"""

def before(values):
    out = []
    for value in values:
        if isinstance(value, str):
            out.append(len(value))
        elif isinstance(value, (list, tuple)):
            out.append(len(value) * 2)
        else:
            out.append(0)
    return out


def after(values):
    out = []
    for value in values:
        kind = type(value)
        if kind is str:
            out.append(len(value))
        elif kind is list or kind is tuple:
            out.append(len(value) * 2)
        else:
            out.append(0)
    return out


def _mixed(n):
    out = []
    for i in range(n):
        if i % 3 == 0:
            out.append(f"s{i}")
        elif i % 3 == 1:
            out.append([i, i + 1])
        else:
            out.append(i)
    return out


def cases():
    return [("large",  lambda: (_mixed(300_000),)),
            ("normal", lambda: (_mixed(3_000),)),
            ("edge",   lambda: ([],))]
