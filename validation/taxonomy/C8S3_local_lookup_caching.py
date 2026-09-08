"""C8.S3 Missing Local Lookup Caching -- an attribute chain resolved per iteration.

Distinct from C3.S2: nothing is *computed*, only resolved. The card claims the
resolution alone is worth hoisting.
"""

class Config:
    def __init__(self):
        self.limits = type("L", (), {"maximum": 100})()


def before(xs, config):
    out = 0
    for x in xs:
        if x < config.limits.maximum:
            out += x
    return out


def after(xs, config):
    maximum = config.limits.maximum
    out = 0
    for x in xs:
        if x < maximum:
            out += x
    return out


def cases():
    return [("large", lambda: (list(range(400_000)), Config())),
            ("small", lambda: (list(range(50)), Config()))]
