"""C6.S2 Unnecessary Copying -- a three-step swap where a tuple assignment does.

The taxonomy's own second example for this root cause, which had no
implementation: `tmp = a; a = b; b = tmp` against `a, b = b, a`.

The tuple form builds and unpacks a two-element tuple, which CPython special-
cases into a stack rotation with no tuple at all; the three-statement form is
three stores and a name that exists only to hold a reference for one bytecode.

Included as the small end of this root cause. The other measured files copy
whole containers, where the saving scales with the data. This one is a fixed
few instructions per swap however large the values are, so it can only show up
on a very hot path -- which is the honest thing for the card to say.
"""


def before(values):
    total = 0
    a, b = 0, 1
    for value in values:
        tmp = a
        a = b
        b = tmp
        total += a + value
    return total


def after(values):
    total = 0
    a, b = 0, 1
    for value in values:
        a, b = b, a
        total += a + value
    return total


def cases():
    return [("many-swaps", lambda: (list(range(1_000_000)),)),
            ("few-swaps",  lambda: (list(range(10_000)),))]
