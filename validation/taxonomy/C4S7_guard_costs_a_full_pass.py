"""C4.S7 Missing Edge-Case Guards -- detecting the fast case
costs a full pass.

`C4S7_algebraic_guard` measures a guard that costs one modulo per element and
skips a trial division, and pays. The guard here has the same shape and a
different price: knowing whether the batch is already sorted means comparing
every adjacent pair, which is the linear scan the guard was meant to save.

On input that is almost never already sorted -- which is most input -- the scan
runs, fails on one of its first comparisons about as often as not, and then the
general path runs anyway. On the `already-sorted` case the guard pays for
itself, which is the reading that says what precondition it needs.

The guard has to be cheaper than what it skips *and* has to fire often enough to
pay for the times it does not. A guard that is O(n) in front of an O(n log n)
body only wins when it succeeds; a guard that is O(1) wins either way.
"""

def _median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def before(batches):
    return [_median(batch) for batch in batches]


def after(batches):
    out = []
    for batch in batches:
        for i in range(1, len(batch)):
            if batch[i - 1] > batch[i]:
                out.append(_median(batch))
                break
        else:
            out.append(batch[len(batch) // 2])     # already sorted: no sort
    return out


def _batches(count, width, ordered):
    if ordered:
        return [list(range(i, i + width)) for i in range(count)]
    return [[(i * 7919 + j * 31) % 1_000 for j in range(width)] for i in range(count)]


def cases():
    return [("never-sorted",   lambda: (_batches(20_000, 40, False),)),
            ("already-sorted", lambda: (_batches(20_000, 40, True),)),
            ("edge",           lambda: ([[1]],))]
