"""C1.S5 Resultless Computation -- a pure call whose result is discarded."""

def before(rows):
    total = 0
    for r in rows:
        sorted(r)                  # result dropped on the floor
        total += r[0]
    return total


def after(rows):
    total = 0
    for r in rows:
        total += r[0]
    return total


def cases():
    return [("large", lambda: ([[3, 1, 2]] * 200_000,)),
            ("small", lambda: ([[3, 1, 2]] * 50,))]
