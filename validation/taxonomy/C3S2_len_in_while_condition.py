"""C3.S2 Recomputing Loop-Invariant Values -- `len()` in a `while` condition.

The taxonomy's own first example for this root cause, which had no
implementation. The measured files hoist a set comprehension, a call and an
attribute chain; the one file with `len()` in a `while` condition is
`C3S7_delete_while_scanning`, where the loop deletes as it goes and the length
genuinely changes, so hoisting it there is a bug.

This is the case the taxonomy names: nothing mutates the list, so the length is
invariant and the hoist is legal. Having both measured is the point -- the two
are textually identical and only reading the body tells them apart.
"""


def before(values):
    total = 0
    i = 0
    while i < len(values):
        total += values[i]
        i += 1
    return total


def after(values):
    total = 0
    i = 0
    n = len(values)
    while i < n:
        total += values[i]
        i += 1
    return total


def cases():
    return [("large",  lambda: (list(range(600_000)),)),
            ("normal", lambda: (list(range(6_000)),))]
