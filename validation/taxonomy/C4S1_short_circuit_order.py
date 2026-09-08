"""C4.S1 Poor Short-Circuit Ordering -- expensive test evaluated first.

`and` stops at the first false, so putting the cheap decisive test first means
the expensive one runs only on what survives.
"""

def _expensive(x):
    return len(str(x * x * x)) > 3


def before(xs, k):
    return [x for x in xs if _expensive(x) and x > k]


def after(xs, k):
    return [x for x in xs if x > k and _expensive(x)]


def cases():
    return [("cheap-test-rejects-most", lambda: (list(range(200_000)), 10**9)),
            ("cheap-test-rejects-none", lambda: (list(range(200_000)), -1))]
