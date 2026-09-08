"""C1.S7 Unnecessary Variable -- a return that goes through a name.

The card calls this the canonical example and says the canonical example is not
worth measuring. Two instructions per call, so the large case is many calls
over a trivial input rather than one call over a large one.
"""

class Row:
    __slots__ = ("gross", "discount")

    def __init__(self, gross, discount):
        self.gross = gross
        self.discount = discount


def before(row, repeats):
    total = 0
    for _ in range(repeats):
        result = row.gross - row.discount
        total += result
    return total


def after(row, repeats):
    total = 0
    for _ in range(repeats):
        total += row.gross - row.discount
    return total


def cases():
    return [("many-calls", lambda: (Row(100, 7), 2_000_000)),
            ("few-calls",  lambda: (Row(100, 7), 100))]
