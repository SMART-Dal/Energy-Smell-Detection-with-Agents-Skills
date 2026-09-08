"""C2.S2 Missing Static Declaration -- the declaration changed and nothing else.

The other C2.S2 case changes two things at once: the declaration *and* the call
site, from `obj.newer(a, b)` to `After.newer(a, b)`. That makes its reading
hard to attribute. Here both variants are called the same way, through
`self.`, so the only difference is the decorator -- which is what the card's
patch shape (`signature`) actually says the repair is.
"""

class Before:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = 0

    def _newer(self, a, b):
        return a if a > b else b

    def run(self, pairs):
        total = 0
        for a, b in pairs:
            total += self._newer(a, b)
        return total


class After:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = 0

    @staticmethod
    def _newer(a, b):
        return a if a > b else b

    def run(self, pairs):
        total = 0
        for a, b in pairs:
            total += self._newer(a, b)
        return total


def before(pairs):
    return Before().run(pairs)


def after(pairs):
    return After().run(pairs)


def cases():
    return [("large",  lambda: ([(i, i + 1) for i in range(500_000)],)),
            ("normal", lambda: ([(i, i + 1) for i in range(5_000)],))]
