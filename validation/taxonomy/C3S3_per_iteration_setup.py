"""C3.S3 Inefficient Per-Iteration Setup -- a set rebuilt every iteration.

From Javad's OveruseOfLoops/SelectDesiredItems, which is the clearest case in
his whole corpus: the set is identical on every pass.
"""

def before(xs, k):
    out = []
    for x in xs:
        allowed = {i for i in range(1, k, 2)}
        if x in allowed:
            out.append(x)
    return out


def after(xs, k):
    allowed = {i for i in range(1, k, 2)}
    out = []
    for x in xs:
        if x in allowed:
            out.append(x)
    return out


def cases():
    return [("large", lambda: (list(range(20_000)), 200)),
            ("small", lambda: (list(range(20)), 200)),
            ("empty", lambda: ([], 200))]
