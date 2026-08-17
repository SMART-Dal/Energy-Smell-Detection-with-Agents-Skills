"""C10.S1 Skipping Optimized Built-ins -- the accumulate-by-hand case.

The card's central claim: a loop that reimplements a builtin should call the
builtin, because the builtin's loop runs in C.
"""

def before(xs):
    total = 0
    for x in xs:
        total += x
    return total


def after(xs):
    return sum(xs)


def cases():
    return [
        ("large", lambda: (list(range(200_000)),)),
        ("small", lambda: (list(range(50)),)),
        ("empty", lambda: ([],)),
    ]
