"""C5.S1 Inefficient Data Structure Choice -- the construction site is in
another method.

The card's second repair example and the shape it says is normal: the waste is
visible in `handle` and fixable only in `__init__`. Still one repair, and the
card warns to check every other use of the attribute first -- here nothing
indexes it or depends on its order, which is what makes a set available rather
than an index beside it.
"""

class BeforeRouter:
    __slots__ = ("blocked",)

    def __init__(self, paths):
        self.blocked = list(paths)

    def handle(self, requests):
        return sum(1 for r in requests if r not in self.blocked)


class AfterRouter:
    __slots__ = ("blocked",)

    def __init__(self, paths):
        self.blocked = set(paths)

    def handle(self, requests):
        return sum(1 for r in requests if r not in self.blocked)


def before(paths, requests):
    return BeforeRouter(paths).handle(requests)


def after(paths, requests):
    return AfterRouter(paths).handle(requests)


def cases():
    return [("large-table", lambda: ([f"/p{i}" for i in range(2_000)],
                                     [f"/p{i % 4000}" for i in range(20_000)])),
            ("small-table", lambda: ([f"/p{i}" for i in range(6)],
                                     [f"/p{i % 12}" for i in range(20_000)])),
            ("edge",        lambda: ([], []))]
