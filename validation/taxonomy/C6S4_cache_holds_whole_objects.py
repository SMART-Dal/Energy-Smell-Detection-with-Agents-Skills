"""C6.S4 Oversized Data Retaining -- a cache holding whole records where an
identifier would do.

The card says the collector-time half is spread over the process and will not
appear in a one-second window, so what a case file can show is the allocation
and the traversal of what was retained. Both are here: the cache is built and
then walked.
"""

class Record:
    __slots__ = ("id", "blob", "meta")

    def __init__(self, i):
        self.id = i
        self.blob = "x" * 512
        self.meta = list(range(16))


def before(records):
    cache = {}
    for record in records:
        cache[record.id] = record
    return sum(r.id for r in cache.values())


def after(records):
    cache = {}
    for record in records:
        cache[record.id] = record.id
    return sum(cache.values())


def cases():
    return [("many",   lambda: ([Record(i) for i in range(60_000)],)),
            ("few",    lambda: ([Record(i) for i in range(60)],)),
            ("edge",   lambda: ([],))]
