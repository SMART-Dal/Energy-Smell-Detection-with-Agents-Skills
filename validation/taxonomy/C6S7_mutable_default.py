"""C6.S7 Leaking Mutable Default Arguments.

The classic bug. It is a correctness defect first, so the two variants are only
equivalent when the default is never relied on across calls -- which is what
makes this a good test of whether the *energy* claim stands on its own.
"""

def _before_impl(x, acc=None):
    if acc is None:
        acc = []
    acc.append(x)
    return len(acc)


def _after_impl(x, acc=None):
    if acc is None:
        acc = []
    acc.append(x)
    return len(acc)


def before(xs):
    return sum(_before_impl(x) for x in xs)


def after(xs):
    return sum(_after_impl(x) for x in xs)


def cases():
    return [("large", lambda: (list(range(200_000)),)),
            ("small", lambda: (list(range(20)),))]
