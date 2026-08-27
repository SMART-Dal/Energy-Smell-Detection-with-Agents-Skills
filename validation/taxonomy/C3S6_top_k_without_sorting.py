"""C3.S6 Unfiltered Bulk Processing -- the top k, without sorting everything.

The card names `heapq.nlargest` as one of its reductions. Sorting n elements to
take k is n log n where a heap of size k is n log k, so the saving is the
selectivity: `k-tiny` takes twenty of four hundred thousand, and `k-most` takes
nearly all of them, where the heap has nothing left to skip.
"""

import heapq


def before(values, k):
    return sorted(values, reverse=True)[:k]


def after(values, k):
    return heapq.nlargest(k, values)


def cases():
    # `nlargest` with k close to n is O(n log k) with a heap almost as big as
    # the input, and at 400_000 it timed out. The crossover is the point, so
    # the shape is kept and the size halved twice over.
    values = [(i * 7919) % 1_000_000 for i in range(100_000)]
    return [("k-tiny", lambda: (list(values), 20)),
            ("k-most", lambda: (list(values), 95_000)),
            ("edge",   lambda: ([], 5))]
