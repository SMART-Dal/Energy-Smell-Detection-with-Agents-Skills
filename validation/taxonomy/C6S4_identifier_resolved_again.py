"""C6.S4 Oversized Data Retaining -- the identifier has to be
resolved back every time it is read.

"Storing full user profile objects in a session cache when only user IDs are
needed for subsequent lookups" is the description's own example, and
`C6S4_cache_holds_whole_objects` measures the projection at +27%. The saving is
the retained bytes and the traversal of them.

An identifier is only smaller if it is not immediately turned back into the
object. Here every read of the cache needs the record, so the repair replaces
one attribute read with a dict probe plus the record, and it does that on every
read rather than once per write. With ten reads per entry the lookups cost more
than the retention saved.

The ratio to weigh is reads against entries. Storing keys wins for a cache that
is written often and read rarely, or where the value is genuinely not needed
again; it loses for a cache that exists to avoid the lookup.
"""

class Record:
    __slots__ = ("id", "blob", "score")

    def __init__(self, i):
        self.id = i
        self.blob = "x" * 256
        self.score = i % 97


def before(records, reads):
    cache = {}
    for record in records:
        cache[record.id] = record
    total = 0
    for key in reads:
        total += cache[key].score
    return total


def after(records, reads):
    source = {record.id: record for record in records}
    cache = {}
    for record in records:
        cache[record.id] = record.id            # only the identifier retained
    total = 0
    for key in reads:
        total += source[cache[key]].score       # resolved again on every read
    return total


def _records(n):
    return [Record(i) for i in range(n)]


def cases():
    return [("read-heavy",  lambda: (_records(20_000), [i % 20_000 for i in range(200_000)])),
            ("write-heavy", lambda: (_records(20_000), [1])),
            ("edge",        lambda: (_records(1), [0]))]
