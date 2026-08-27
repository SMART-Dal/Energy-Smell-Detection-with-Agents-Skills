"""C5.S2 Missing Helper Type -- the index goes stale between
the queries it was built for.

"Repeatedly scanning a list to find matching entries instead of building a dict
index once" is the description, and `C5S2_missing_index` measures the index at
+99.5% over many queries. The word doing the work is *once*.

The records here are appended to between queries, so an index built before the
loop answers the later queries from a snapshot. Rebuilding it after every change
-- which is what keeps the answers right -- means one full pass over the records
per query, which is the linear scan the index replaced, plus the hashing and the
dict.

The card's obligation is the whole finding: an index is a second copy of the
truth, and it is only cheaper than scanning if the data holds still. Where the
collection is mutated between reads, "build an index" is either wrong or is the
same cost with more code.
"""

def before(records, queries):
    found = 0
    for query in queries:
        records.append((f"new-{query}", 1))
        for name, value in records[:len(records) - 1]:
            if name == query:
                found += value
                break
    return found


def after(records, queries):
    found = 0
    for query in queries:
        records.append((f"new-{query}", 1))
        index = dict(records[:len(records) - 1])   # rebuilt, because it changes
        if query in index:
            found += index[query]
    return found


def _records(n):
    return [(f"k{i}", i) for i in range(n)]


def cases():
    return [("many-queries", lambda: (_records(2_000), [f"k{i % 2000}" for i in range(400)])),
            ("few-queries",  lambda: (_records(2_000), [f"k{i}" for i in range(4)])),
            ("edge",         lambda: (_records(1), []))]
