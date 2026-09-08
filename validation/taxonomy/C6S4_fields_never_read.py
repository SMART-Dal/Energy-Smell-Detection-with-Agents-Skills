"""C6.S4 Oversized Data Retaining -- rows kept with fields nothing consults.

The card says to read the code that *reads* the retained data: if only one
field is ever consulted, the rest is kept for nothing. The repair projects at
the point of retention rather than at the point of use, which is why it belongs
here rather than in C9.S2 -- nothing crosses a process boundary.
"""

def before(rows):
    kept = [dict(row) for row in rows]
    return sum(r["id"] for r in kept)


def after(rows):
    kept = [row["id"] for row in rows]
    return sum(kept)


def _rows(n):
    return [{"id": i, "blob": "x" * 256, "tags": [1, 2, 3], "note": f"n{i}"}
            for i in range(n)]


def cases():
    return [("many",  lambda: (_rows(60_000),)),
            ("few",   lambda: (_rows(60),))]
