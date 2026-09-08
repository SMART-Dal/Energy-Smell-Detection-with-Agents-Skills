"""C7.S4 Inefficient Operation Ordering -- and a test of `sort_then_slice`.

From Javad's BuiltInBehavior/SumTopK, whose own refactoring is not
behaviour-preserving (it sorts the caller's list in place). The repair that
*is* equivalent is a bounded heap: n log k instead of n log n.
"""

import heapq


def before(xs, k):
    return sum(sorted(xs)[:k])


def after(xs, k):
    return sum(heapq.nsmallest(k, xs))


def cases():
    return [
        ("k-tiny-n-large", lambda: ([(i * 7919) % 1_000_003 for i in range(400_000)], 100)),
        ("k-near-n", lambda: ([(i * 7919) % 1_000_003 for i in range(20_000)], 19_000)),
    ]
