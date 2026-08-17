"""C10.S1 -- the same claim, but where the builtin is `collections.Counter`.

Javad's OveruseOfLoops/OccurenceOfOddItems1 sample runs this comparison in the
*opposite* direction: it treats the hand-written dict loop as the improvement
over Counter. If that is right, C10.S1 is narrower than its card says, and the
card must name the exception.
"""

from collections import Counter


def before(xs):
    counts = {}
    for x in xs:
        seen = counts.get(x, -1)
        counts[x] = seen + 1 if seen != -1 else 1
    return counts


def after(xs):
    return dict(Counter(xs))


def cases():
    return [
        ("many-duplicates", lambda: ([i % 500 for i in range(200_000)],)),
        ("all-distinct", lambda: (list(range(200_000)),)),
        ("empty", lambda: ([],)),
    ]
