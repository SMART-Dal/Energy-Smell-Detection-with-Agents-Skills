"""C3.S2 Loop-Invariant Computation -- a set rebuilt on every iteration.

The card's first repair example and what it calls the large form: what was
hoisted is O(k) work, so the saving is len(values) * k rather than a few
bytecodes. `k-small` shrinks the invariant so the card can say how heavy it has
to be before the hoist is worth reporting.
"""

def before(values, k):
    result = []
    for x in values:
        allowed = {i for i in range(1, k, 2)}
        if x in allowed:
            result.append(x)
    return result


def after(values, k):
    allowed = {i for i in range(1, k, 2)}
    result = []
    for x in values:
        if x in allowed:
            result.append(x)
    return result


def cases():
    # 20_000 x 400 rebuilt-set elements per call was 8M operations and timed
    # out at ten minutes. The claim is unchanged; only the arithmetic fits.
    return [("k-large", lambda: (list(range(4_000)), 200)),
            ("k-small", lambda: (list(range(4_000)), 4)),
            ("edge",    lambda: ([], 200))]
