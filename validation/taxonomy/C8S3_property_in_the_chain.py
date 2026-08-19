"""C8.S3 Repeated Attribute/Method Lookup -- a property in the chain.

The card says that if a link in the chain *computes*, the saving is much larger
than a dict lookup -- and warns the semantics may differ, because the property
was being re-evaluated on purpose. Here nothing rebinds it during the loop, so
hoisting is safe, and the reading says how much a computing link is worth
against a plain one.
"""

class Limits:
    __slots__ = ("_batch",)

    def __init__(self, batch):
        self._batch = batch

    @property
    def batch(self):
        return self._batch * 1              # a property, not a stored attribute


class Config:
    __slots__ = ("limits",)

    def __init__(self, batch):
        self.limits = Limits(batch)


def before(config, rows):
    kept = 0
    for row in rows:
        if row < config.limits.batch:
            kept += 1
    return kept


def after(config, rows):
    batch = config.limits.batch
    kept = 0
    for row in rows:
        if row < batch:
            kept += 1
    return kept


def cases():
    return [("large",  lambda: (Config(500_000), list(range(1_000_000)))),
            ("normal", lambda: (Config(5_000), list(range(10_000)))),
            ("edge",   lambda: (Config(1), []))]
