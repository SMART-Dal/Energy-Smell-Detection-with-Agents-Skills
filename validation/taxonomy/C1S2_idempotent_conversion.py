"""C1.S2 Redundant Assignment -- an idempotent call, not merely a store.

The card carries this as its stated exception: a redundant *store* is one to
three instructions and cannot scale, but a redundant *call* is not free, and
`int()` on something already an int is a global lookup and a type check per
element. This measures whether that exception is real.
"""

def before(values):
    total = 0
    for value in values:
        value = int(value)               # already an int on every element
        total += value
    return total


def after(values):
    total = 0
    for value in values:
        total += value
    return total


def cases():
    return [("large",  lambda: (list(range(1_000_000)),)),
            ("normal", lambda: (list(range(10_000)),)),
            ("edge",   lambda: ([],))]
