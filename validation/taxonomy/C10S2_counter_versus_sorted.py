"""C10.S2 Suboptimal Built-in Choice -- `Counter` against `sorted` for multiset
equality.

`Counter` is asymptotically better -- one pass against a sort -- and on short
sequences it loses badly, because two dicts have to be built and hashed where
two tiny sorts are a handful of comparisons in C. This was measured at twelve
times slower on five-element lists while it was misfiled as a C4.S5 case; here
it is asked properly, with the sequence length as the variable, so the card can
say roughly where the crossover sits.

`before` is `sorted`, so a negative reading means `sorted` wins.
"""

from collections import Counter


def before(pairs):
    return sum(1 for a, b in pairs if sorted(a) == sorted(b))


def after(pairs):
    return sum(1 for a, b in pairs if Counter(a) == Counter(b))


def _pairs(count, width):
    a = list(range(width))
    b = list(reversed(a))
    return ([(a, b)] * count,)


def cases():
    # 100_000 pairs of five elements meant 200_000 sorts or 200_000 Counters
    # per call, which timed out. The crossover is what matters, not the count.
    return [("short-sequences", lambda: _pairs(20_000, 5)),
            ("long-sequences",  lambda: _pairs(200, 2_000)),
            ("edge",            lambda: ([],))]
