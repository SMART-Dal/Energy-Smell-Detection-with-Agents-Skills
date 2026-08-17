"""C3.S7 Inefficient Array Mutation in Loop -- removing from a list while scanning.

`list.remove` is a linear scan plus a memmove, so the loop is quadratic. The
repair builds the survivors instead.
"""

def before(xs, k):
    keep = list(xs)
    for x in list(keep):
        if x % k == 0:
            keep.remove(x)
    return keep


def after(xs, k):
    return [x for x in xs if x % k != 0]


def cases():
    return [("large", lambda: (list(range(20_000)), 3)),
            ("small", lambda: (list(range(20)), 3)),
            ("empty", lambda: ([], 3))]
