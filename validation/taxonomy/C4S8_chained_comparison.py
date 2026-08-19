"""C4.S8 Non-Idiomatic Constructs -- a chained comparison, and the branches it
makes redundant.

`a < b < c` evaluates `b` once where `a < b and b < c` evaluates it twice --
and here the whole four-branch structure collapses too, because the first test
and the `elif` are both implied by the range comparison. The card says that
part is C4.S2 and that the two together are one repair; this file measures the
edit as it would actually be committed.

`b` is a call rather than a name, so evaluating it twice costs something: with
a plain local the interpreter's second load is nearly free and the card's claim
would be untestable.
"""

def _position(row):
    return (row * 7919) % 1000


def before(rows, low, high):
    hits = 0
    for row in rows:
        if _position(row) < low:
            pass
        elif low <= _position(row) and _position(row) <= high:
            hits += 1
        elif _position(row) > high:
            pass
    return hits


def after(rows, low, high):
    hits = 0
    for row in rows:
        if low <= _position(row) <= high:
            hits += 1
    return hits


def cases():
    return [("large",  lambda: (list(range(300_000)), 100, 900)),
            ("normal", lambda: (list(range(3_000)), 100, 900)),
            ("edge",   lambda: ([], 100, 900))]
