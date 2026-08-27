"""C5.S1 Inefficient Data Structure Choice -- a heap built and then drained
completely.

From Javad's ImproperDataStructure/BuildSortedListBasedOnOccurence, where the
refactoring replaces `heapq` with `sorted`.

A heap is the right container when the question is "the smallest one", asked a
few times against a collection that keeps changing. Draining it to empty asks
for every element in order, which is a sort -- done as N interpreted
`heappush` calls and N interpreted `heappop` calls, each of which sifts through
log N Python-level comparisons. `sorted` does the whole thing in one C call.

Same elements, same order out. What changes is whether the ordering work happens
in the interpreter or under it, and the card's own test -- which operation does
the hot path actually perform -- is what separates the two.
"""

import heapq


def before(occurrences):
    heap = []
    for item, count in occurrences:
        heapq.heappush(heap, (item, count))
    out = []
    while heap:
        item, count = heapq.heappop(heap)
        out.extend([item] * count)
    return out


def after(occurrences):
    out = []
    for item, count in sorted(occurrences, key=lambda pair: pair[0]):
        out.extend([item] * count)
    return out


def _occurrences(n):
    return [((i * 7919) % 1_000_003, (i % 3) + 1) for i in range(n)]


def cases():
    return [("many-items", lambda: (_occurrences(200_000),)),
            ("few-items",  lambda: (_occurrences(20),)),
            ("edge",       lambda: ([],))]
