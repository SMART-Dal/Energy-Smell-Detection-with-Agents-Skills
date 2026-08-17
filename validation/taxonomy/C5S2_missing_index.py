"""C5.S2 Missing Helper Type -- repeated scans where an index should be built."""

def before(rows, queries):
    out = []
    for q in queries:
        for name, value in rows:
            if name == q:
                out.append(value)
                break
    return out


def after(rows, queries):
    index = dict(rows)
    return [index[q] for q in queries if q in index]


def cases():
    rows = [(f"k{i}", i) for i in range(2_000)]
    return [("many-queries", lambda: (list(rows), [f"k{i}" for i in range(0, 2000, 2)])),
            ("one-query", lambda: (list(rows), ["k1999"])),
            ("empty", lambda: ([], []))]
