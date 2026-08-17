"""C8.S1 Missing Memoization Cache -- a pure function recomputed on repeats.

From Javad's NotCaching/IdentifyListPrimes. The `all-distinct` case is the
adversarial one: with no repeats the cache is pure overhead, and the card has
to say so.
"""

def _is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def before(xs):
    return [_is_prime(x) for x in xs]


def after(xs):
    seen = {}
    out = []
    for x in xs:
        if x not in seen:
            seen[x] = _is_prime(x)
        out.append(seen[x])
    return out


def cases():
    return [("many-repeats", lambda: ([(i % 300) + 10_000 for i in range(30_000)],)),
            ("all-distinct", lambda: (list(range(10_000, 40_000)),)),
            ("empty", lambda: ([],))]
