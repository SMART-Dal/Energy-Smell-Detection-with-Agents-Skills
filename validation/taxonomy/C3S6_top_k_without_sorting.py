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
    values = [(i * 7919) % 1_000_000 for i in range(400_000)]
    return [("k-tiny", lambda: (list(values), 20)),
            ("k-most", lambda: (list(values), 380_000)),
            ("edge",   lambda: ([], 5))]
