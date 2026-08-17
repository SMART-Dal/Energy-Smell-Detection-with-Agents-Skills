"""C10.S5 Inefficient Scope Lookup -- and a test of my own new analyzer.

`global_lookup_in_loop` was added in this pass and has never been measured. It
claims that binding a repeatedly-read global to a local above the loop saves
real energy. If it does not, the rule ships noise into every arm.

The threshold in the rule is three reads per iteration, so the `before` here
uses exactly that.
"""

SCALE = 3
OFFSET = 7


def before(xs):
    out = []
    for x in xs:
        out.append(x * SCALE + OFFSET - SCALE)
    return out


def after(xs):
    scale = SCALE
    offset = OFFSET
    out = []
    for x in xs:
        out.append(x * scale + offset - scale)
    return out


def cases():
    return [
        ("large", lambda: (list(range(300_000)),)),
        ("small", lambda: (list(range(50)),)),
        ("empty", lambda: ([],)),
    ]
