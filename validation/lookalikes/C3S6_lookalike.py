"""C3.S6 Unfiltered Bulk Iteration -- LOOKS THE SAME, IS NOT: the first ten are not the
top ten.

"Only the first N results are consumed, so stop after N" is the description's
own example, and `C3S6_unfiltered_bulk` measures the reduction at +87.2%.

The consumer here wants the ten largest, which is a question about all the
elements. `islice` gives the first ten in input order, which are ten arbitrary
elements. The repair reads as a reduction and is a change of answer.

The clause that decides it is "only a subset ... is needed for the final
result". A subset that depends on a global property of the collection -- largest,
median, most frequent, unique -- is not a subset the iteration can stop early
for. `heapq.nlargest` is the reduction that applies, and it is still a full pass.
"""

from itertools import islice


def _weight(row):
    return sum(ord(c) for c in row) % 9_973


def before(rows, k):
    return sorted((_weight(r) for r in rows), reverse=True)[:k]


def after(rows, k):
    return list(islice((_weight(r) for r in rows), k))


def cases():
    rows = [f"row-{i}-{i * 7919 % 100_000}" for i in range(200_000)]
    return [("top-few", lambda: (list(rows), 10)),
            ("top-all", lambda: (list(rows), 200_000)),
            ("edge",    lambda: ([], 5))]
