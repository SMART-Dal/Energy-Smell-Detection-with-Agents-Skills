"""C7.S5 Unsimplified Operation -- `abs` on a difference that cannot be
negative.

From the project's sample set, and the card's own worked fact: `k` is the
larger of the two values, so `k - value` is never negative and `abs` cannot
change it. The card insists the fact must hold for *every* input the function
accepts, which it does here by construction -- `k` comes from `max`.

`abs-needed` removes that guarantee by passing an arbitrary `k`, where the
simplification would be wrong; it is measured only to show the two are not the
same function, and `after` keeps `abs` on that path.
"""

def before(first, second, use_max):
    total = 0
    for a, b in zip(first, second):
        k = max(a, b) if use_max else a
        total += abs(k - b)
    return total


def after(first, second, use_max):
    total = 0
    for a, b in zip(first, second):
        if use_max:
            k = max(a, b)
            total += k - b                 # non-negative by construction
        else:
            total += abs(a - b)
    return total


def cases():
    first = [(i * 7919) % 10_000 for i in range(400_000)]
    second = [(i * 104_729) % 10_000 for i in range(400_000)]
    return [("abs-removable", lambda: (first, second, True)),
            ("abs-needed",    lambda: (first, second, False)),
            ("edge",          lambda: ([], [], True))]
