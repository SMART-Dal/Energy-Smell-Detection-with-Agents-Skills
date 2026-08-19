"""C7.S4 Inefficient Operation Order -- the transform runs on the survivors.

The card says the saving scales with selectivity and is nothing when the cheap
step removes nothing, so the two cases put the filter's pass rate on either
side. Commutation holds here because the predicate reads the *input*, not the
transform's output -- which is the one way this repair usually fails.
"""

def _expensive(row):
    total = 0
    for i in range(1, 30):
        total += (row * i) % 11
    return total


def before(rows, floor):
    scored = [_expensive(r) for r in rows]
    return [s for r, s in zip(rows, scored) if r > floor]


def after(rows, floor):
    return [_expensive(r) for r in rows if r > floor]


def cases():
    rows = [(i * 7919) % 1_000 for i in range(120_000)]
    return [("selective",   lambda: (list(rows), 950)),
            ("unselective", lambda: (list(rows), -1)),
            ("edge",        lambda: ([], 0))]
