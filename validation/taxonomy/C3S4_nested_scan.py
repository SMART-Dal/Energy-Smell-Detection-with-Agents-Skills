"""C3.S4 Inefficient Nested Iteration -- an inner linear scan over a second list.

The repair removes a loop level by hashing, so this is the quadratic-to-linear
claim. It should confirm strongly; if it does not, the rig is wrong.
"""

def before(xs, ys):
    return [x for x in xs if x in ys]


def after(xs, ys):
    lookup = set(ys)
    return [x for x in xs if x in lookup]


def cases():
    return [("large", lambda: (list(range(3_000)), list(range(1_000, 4_000)))),
            ("small", lambda: (list(range(20)), list(range(10, 30))))]
