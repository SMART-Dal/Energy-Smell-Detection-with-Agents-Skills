"""C8.S1 Missing Memoization Cache -- normalising the key doubles the hit rate.

From the project's sample set. `(x, y)` and `(y, x)` are different keys for a
symmetric function, so sorting the pair before looking it up halves the misses
for free -- a detail the card calls out and nothing has measured. Both variants
memoise; only the key differs, which isolates the normalisation from the
caching.
"""

def _expensive(a, b):
    # Symmetric in its arguments -- which is the precondition for normalising
    # the key, and was wrong on the first attempt: `(a * i + b)` is not.
    total = 0
    for i in range(1, 40):
        total += (a * b + i) % 17
    return total


def before(pairs):
    memo = {}
    total = 0
    for a, b in pairs:
        key = (a, b)
        if key not in memo:
            memo[key] = _expensive(a, b)
        total += memo[key]
    return total


def after(pairs):
    memo = {}
    total = 0
    for a, b in pairs:
        key = (a, b) if a <= b else (b, a)
        if key not in memo:
            memo[key] = _expensive(min(a, b), max(a, b))
        total += memo[key]
    return total


def cases():
    # Symmetric pairs, so half of them are the mirror of one already seen.
    pairs = [((i * 7) % 60, (i * 13) % 60) for i in range(200_000)]
    ordered = [(a, b) if a <= b else (b, a) for a, b in pairs]
    return [("mirrored-pairs", lambda: (list(pairs),)),
            ("already-sorted", lambda: (list(ordered),)),
            ("edge",           lambda: ([],))]
