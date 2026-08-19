"""C8.S3 Repeated Attribute/Method Lookup -- the chain, in a body that does
real work.

The card's third `NOT a smell when` clause seen from the measurement side: the
same three-link chain, hoisted the same way, in a loop that also formats a
string. If the saving disappears here and not in the property case, the card
can say what proportion of the body the lookups have to be.
"""

class Limits:
    __slots__ = ("batch",)

    def __init__(self, batch):
        self.batch = batch


class Config:
    __slots__ = ("limits",)

    def __init__(self, batch):
        self.limits = Limits(batch)


def before(config, rows):
    out = []
    for row in rows:
        out.append(f"{row:>10}:{config.limits.batch}")
    return len(out)


def after(config, rows):
    batch = config.limits.batch
    out = []
    for row in rows:
        out.append(f"{row:>10}:{batch}")
    return len(out)


def cases():
    return [("large",  lambda: (Config(7), list(range(400_000)))),
            ("normal", lambda: (Config(7), list(range(4_000)))),
            ("edge",   lambda: (Config(7), []))]
