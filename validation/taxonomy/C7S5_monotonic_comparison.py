"""C7.S5 Unsimplified Operation -- a monotonic transform inside a comparison.

`math.sqrt` is strictly increasing on non-negative reals, so `sqrt(a) > sqrt(b)`
and `a > b` agree wherever both are defined. The result *is* consumed -- which
is what separates this from a discarded computation -- and the operation itself
got cheaper, which is what this root cause is.

`has-negatives` removes the precondition: `sqrt` raises there, so the two
functions are not the same and `after` keeps the calls on that path.
"""

import math


def before(pairs, non_negative):
    hits = 0
    for a, b in pairs:
        if non_negative:
            if math.sqrt(a) > math.sqrt(b):
                hits += 1
        elif a >= 0 and b >= 0 and math.sqrt(a) > math.sqrt(b):
            hits += 1
    return hits


def after(pairs, non_negative):
    hits = 0
    for a, b in pairs:
        if non_negative:
            if a > b:                       # sqrt is strictly increasing
                hits += 1
        elif a >= 0 and b >= 0 and math.sqrt(a) > math.sqrt(b):
            hits += 1
    return hits


def cases():
    pairs = [((i * 7919) % 10_000, (i * 104_729) % 10_000) for i in range(400_000)]
    mixed = [(a - 5_000, b) for a, b in pairs]
    return [("non-negative",  lambda: (pairs, True)),
            ("has-negatives", lambda: (mixed, False))]
