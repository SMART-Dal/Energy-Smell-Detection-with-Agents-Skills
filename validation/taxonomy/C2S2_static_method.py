"""C2.S2 Missing Static Declaration -- a method that never touches `self`.

The card says such a method should be `@staticmethod`, which skips binding a
method object per call. Javad's ObjectOriented/StaticMethodCreation sample
rewrites in the *opposite* direction, from a staticmethod to an instance
method, implying the measurement went the other way.

The analyzer `method_ignores_self` fires 657 times on pandas, so if this claim
does not hold the cost of being wrong is large.
"""


class Before:
    def __init__(self, year):
        self.year = year

    def newer(self, a, b):
        return a.year > b.year


class After:
    def __init__(self, year):
        self.year = year

    @staticmethod
    def newer(a, b):
        return a.year > b.year


def before(n, a, b):
    obj = Before(0)
    hits = 0
    for _ in range(n):
        hits += obj.newer(a, b)
    return hits


def after(n, a, b):
    hits = 0
    for _ in range(n):
        hits += After.newer(a, b)
    return hits


def cases():
    return [
        ("many-calls", lambda: (200_000, Before(1990), Before(1980))),
        ("few-calls", lambda: (50, Before(1990), Before(1980))),
    ]
