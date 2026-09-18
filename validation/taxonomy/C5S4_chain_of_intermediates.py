"""C5.S4 Unnecessary Representation Change -- three containers where one will do.

The card's central example. `list(records)` materialises the input, the
comprehension materialises the names, and `set` materialises them again before
the sort. None is read more than once, so each is a full pass and a full
allocation buying nothing.

The `set` survives the repair, because it is the one container doing work:
removing duplicates before the sort. That is the distinction the root cause
turns on -- a conversion is waste only when nothing downstream needed the shape.
"""


def before(records):
    rows = list(records)
    names = [r["name"] for r in rows]
    return sorted(set(names))


def after(records):
    return sorted({r["name"] for r in records})


def _records(n, distinct):
    return [{"name": f"name{i % distinct}", "id": i} for i in range(n)]


def cases():
    return [("dense-duplicates", lambda: (_records(200_000, 500),)),
            ("all-distinct",     lambda: (_records(200_000, 200_000),))]
