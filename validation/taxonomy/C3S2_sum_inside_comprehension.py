"""C3.S2 Loop-Invariant Computation -- the invariant is inside a comprehension,
and quadratic.

From the project's sample set: two versions of `softmax` differ only in where
`sum` sits. A comprehension's *body* runs once per element, so
`sum(exponentials)` is a full pass per element and a function that reads as
linear is quadratic. The rule that clears `for i in range(len(xs))` -- an
iterable is evaluated once -- does not clear this one.
"""

import math


def before(values):
    exponentials = [math.exp(v) for v in values]
    return round(sum(x / sum(exponentials) for x in exponentials), 6)


def after(values):
    exponentials = [math.exp(v) for v in values]
    total = sum(exponentials)
    return round(sum(x / total for x in exponentials), 6)


def cases():
    return [("large",  lambda: ([(i % 50) / 10.0 for i in range(4_000)],)),
            ("normal", lambda: ([(i % 50) / 10.0 for i in range(400)],)),
            ("edge",   lambda: ([1.0],))]
