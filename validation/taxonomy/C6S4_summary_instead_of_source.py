"""C6.S4 Oversized Data Retention -- keeping a total instead of the rows.

The card's second repair, and the only one here that is a genuine trade rather
than a strict improvement: summing at construction retains one number instead
of every row, but it moves the work earlier and makes it unconditional.

So the reading depends entirely on whether the consumer is called. `reported`
asks for the headline on every object, where the repair should win; `unused`
builds the same objects and asks nothing, where eager summing is pure loss and
the honest verdict is a regression.
"""


class BeforeReport:
    __slots__ = ("rows",)

    def __init__(self, rows):
        self.rows = rows

    def headline(self):
        return sum(r["amount"] for r in self.rows)


class AfterReport:
    __slots__ = ("total",)

    def __init__(self, rows):
        self.total = sum(r["amount"] for r in rows)

    def headline(self):
        return self.total


def before(batches, ask):
    total = 0
    for rows in batches:
        report = BeforeReport(rows)
        if ask:
            total += report.headline()
    return total


def after(batches, ask):
    total = 0
    for rows in batches:
        report = AfterReport(rows)
        if ask:
            total += report.headline()
    return total


def _batches(count, width):
    rows = [{"amount": i, "note": f"n{i}"} for i in range(width)]
    return [list(rows) for _ in range(count)]


def cases():
    return [("reported", lambda: (_batches(400, 500), True)),
            ("unused",   lambda: (_batches(400, 500), False))]
