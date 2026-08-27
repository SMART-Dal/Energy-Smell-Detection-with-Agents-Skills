"""C7.S2 Inefficient Problem Decomposition -- exhaustive enumeration where a
bound settles most candidates.

The taxonomy's own example is "trying every possible combination of parameters
exhaustively when simple bound checks could prune 90% of candidates", and it
does not say the enumeration has to be recursive. This one is three nested
loops.

`before` forms every ascending triple and tests it. `after` keeps the same three
loops and the same test, and adds one sound bound: the values are sorted
ascending and non-negative, so once `a[i] + a[j] + a[j+1]` already exceeds the
target no larger `k` can help, and the innermost loop can stop. Nothing is
skipped that could have been a hit.

`loose-target` puts the target above every reachable sum, so the bound never
fires and the check is pure overhead -- which is the reading that says a bound
is only worth adding where it actually cuts.
"""

def before(values, target):
    n = len(values)
    hits = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if values[i] + values[j] + values[k] == target:
                    hits += 1
    return hits


def after(values, target):
    n = len(values)
    hits = 0
    for i in range(n):
        for j in range(i + 1, n):
            base = values[i] + values[j]
            if base >= target:
                break                  # sorted ascending: larger j cannot help
            for k in range(j + 1, n):
                total = base + values[k]
                if total > target:
                    break              # sorted ascending: larger k cannot help
                if total == target:
                    hits += 1
    return hits


def cases():
    values = sorted((i * 7919) % 4_000 for i in range(320))
    return [("tight-target", lambda: (list(values), 900)),
            ("loose-target", lambda: (list(values), 11_000)),
            ("edge",         lambda: ([1, 2, 3], 6))]
