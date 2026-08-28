"""C4.S8 Non-Idiomatic Constructs -- `a < b and b < c` against `a < b < c`.

An earlier version of this file also collapsed a four-branch structure with two
`pass` arms, so `before` evaluated `_position(row)` up to four times a pass and
`after` once. It read +55.2%, and almost all of that was the three calls it
stopped making -- which is C1.S4, not this card. The number could not be
attributed to the construct.

Now the two forms evaluate `_position(row)` the same number of times except for
the one the chain exists to save: `a < b and b < c` evaluates `b` twice,
`a < b < c` evaluates it once. That single duplicated evaluation is the whole
finding, and it is what the card should claim.

`_position` is a call rather than a name on purpose. With a plain local the
interpreter's second `LOAD_FAST` is nearly free and the claim would be
untestable; with a call, evaluating `b` twice costs a frame.
"""

def _position(row):
    return (row * 7919) % 1000


def before(rows, low, high):
    hits = 0
    for row in rows:
        if low <= _position(row) and _position(row) <= high:
            hits += 1
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
