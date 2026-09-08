"""C6.S4 Oversized Data Retaining -- keeping whole records when one field is used."""

def before(rows):
    kept = []
    for r in rows:
        kept.append(r)
    return sum(r["id"] for r in kept)


def after(rows):
    kept = []
    for r in rows:
        kept.append(r["id"])
    return sum(kept)


def cases():
    row = {"id": 1, "blob": "x" * 512, "meta": list(range(32))}
    return [("large", lambda: ([dict(row) for _ in range(50_000)],)),
            ("small", lambda: ([dict(row) for _ in range(20)],))]
