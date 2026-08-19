"""C1.S4 Repeated Computation -- an attribute chain re-derived on two lines.

The card calls this the small form: four dict lookups become two plus one array
read, per call. It is here to put a number on "advisory unless genuinely hot",
so the large case is many calls rather than one big input.
"""

class Config:
    __slots__ = ("limits",)

    def __init__(self, batch):
        self.limits = Limits(batch)


class Limits:
    __slots__ = ("batch",)

    def __init__(self, batch):
        self.batch = batch


def before(config, rows, repeats):
    kept = 0
    for _ in range(repeats):
        if len(rows) > config.limits.batch:
            kept += len(rows[: config.limits.batch])
        else:
            kept += len(rows)
    return kept


def after(config, rows, repeats):
    kept = 0
    for _ in range(repeats):
        batch = config.limits.batch
        if len(rows) > batch:
            kept += len(rows[:batch])
        else:
            kept += len(rows)
    return kept


def cases():
    return [("many-calls", lambda: (Config(4), [0, 1, 2, 3, 4, 5], 300_000)),
            ("few-calls",  lambda: (Config(4), [0, 1, 2, 3, 4, 5], 50)),
            ("edge",       lambda: (Config(4), [], 10))]
