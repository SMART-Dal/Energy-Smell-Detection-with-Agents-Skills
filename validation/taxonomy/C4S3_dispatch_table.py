"""C4.S3 Deep Conditional Nesting -- a comparison chain that is really a table.

The card says this is the measurable form of C4.S3 and that guard-clause
flattening is not. The arms are exhaustive and keyed on a dense integer, which
is the precondition; `_TYPES` at module scope also removes a per-call build,
which the card notes is C5.S3 and subsumed here.
"""

_TYPES = ("red", "blue", "green", "yellow")


def before(numbers):
    out = []
    for number in numbers:
        if number % 4 == 0:
            out.append("red")
        elif number % 4 == 1:
            out.append("blue")
        elif number % 4 == 2:
            out.append("green")
        else:
            out.append("yellow")
    return out


def after(numbers):
    return [_TYPES[number % 4] for number in numbers]


def cases():
    return [("large",  lambda: (list(range(500_000)),)),
            ("normal", lambda: (list(range(5_000)),)),
            ("edge",   lambda: ([],))]
