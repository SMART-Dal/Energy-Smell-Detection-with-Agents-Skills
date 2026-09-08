"""C3.S4 Inefficient Nested Iteration -- the symmetric form, which can lose.

The card's second repair example and its own counter-example in one file. When
the per-pair work is expensive -- `math.gcd` here -- halving the pairs halves
the expensive part and pays. When it is cheap, the mirroring writes cost more
than the comparisons saved, which is what this project measured on a
triangular-with-append sample.

`expensive-pairs` and `cheap-pairs` are the two sides; the gap is the finding.
"""

import math


def before(limit, expensive):
    result = {}
    for i in range(2, limit):
        for j in range(2, limit):
            ok = math.gcd(i, j) == 1 if expensive else (i != j)
            if ok:
                result.setdefault(i, []).append(j)
    return sum(len(v) for v in result.values())


def after(limit, expensive):
    result = {}
    for i in range(2, limit):
        for j in range(i + 1, limit):
            ok = math.gcd(i, j) == 1 if expensive else (i != j)
            if ok:
                result.setdefault(i, []).append(j)
                result.setdefault(j, []).append(i)
    return sum(len(v) for v in result.values())


def cases():
    return [("expensive-pairs", lambda: (400, True)),
            ("cheap-pairs",     lambda: (400, False))]
