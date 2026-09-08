"""C4.S2 Redundant Conditional Evaluation -- the determined test stands in
front of a whole scan.

The card calls this the form worth reporting: `abs(x)` is never negative, so
`abs(x) + k > 0` cannot reject anything once `k > 0`, and what the repair skips
is the entire pass rather than a comparison. `k-negative` is the case where the
fact does not hold and the scan has to happen.
"""

def before(values, k):
    return len([1 for x in values if abs(x) + k > 0])


def after(values, k):
    if k > 0:
        return len(values)
    return len([1 for x in values if abs(x) + k > 0])


def cases():
    return [("k-positive", lambda: ([(i * 7919) % 2001 - 1000 for i in range(400_000)], 5)),
            ("k-negative", lambda: ([(i * 7919) % 2001 - 1000 for i in range(400_000)], -5))]
