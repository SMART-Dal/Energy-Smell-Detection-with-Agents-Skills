"""C1.S3 Redundant Control Flow -- a branch that only rebuilds the condition's own value.

`if c: return True else: return False` collapses to `return c`. The analyzer
grades this DEFINITE, which is a strong word for something the card says is
too small to measure. Both cannot be right about how much it matters.
"""


def before(xs, k):
    hits = 0
    for x in xs:
        if _over(x, k):
            hits += 1
    return hits


def after(xs, k):
    hits = 0
    for x in xs:
        if _over_direct(x, k):
            hits += 1
    return hits


def _over(x, k):
    if x > k:
        return True
    else:
        return False


def _over_direct(x, k):
    return x > k


def cases():
    return [
        ("large", lambda: (list(range(500_000)), 250_000)),
        ("small", lambda: (list(range(50)), 25)),
    ]
