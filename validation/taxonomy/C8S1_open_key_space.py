"""C8.S1 Missing Memoization Cache -- the key space is the whole finding.

The card says the ratio of distinct inputs to calls decides whether this is a
saving or a regression, and that an unbounded cache on user-supplied keys is a
leak. `all-distinct` is the regression: a million computations *plus* a million
dict insertions, and a table holding every result.

`before` is the uncached version, so a negative reading is the cache costing
more than it saves.
"""

def _expensive(x):
    total = 0
    for i in range(1, 40):
        total += (x * i) % 17
    return total


def before(values):
    return sum(_expensive(v) for v in values)


def after(values):
    memo = {}
    total = 0
    for value in values:
        if value not in memo:
            memo[value] = _expensive(value)
        total += memo[value]
    return total


def cases():
    return [("few-distinct", lambda: ([i % 400 for i in range(200_000)],)),
            ("all-distinct", lambda: (list(range(200_000)),)),
            ("edge",         lambda: ([],))]
