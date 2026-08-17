"""C12.S4 Inefficient Array Declaration Order -- advisory.

In a language with struct layout this is real. In Python object attributes are
a dict or a slots tuple and declaration order buys essentially nothing, which
is why the card marks it advisory. This measures whether that is right.
"""

class Before:
    __slots__ = ("cold_a", "cold_b", "cold_c", "hot")

    def __init__(self):
        self.cold_a = self.cold_b = self.cold_c = 0
        self.hot = 1


class After:
    __slots__ = ("hot", "cold_a", "cold_b", "cold_c")

    def __init__(self):
        self.hot = 1
        self.cold_a = self.cold_b = self.cold_c = 0


def before(objs):
    return sum(o.hot for o in objs)


def after(objs):
    return sum(o.hot for o in objs)


def cases():
    return [("many-objects", lambda: ([Before() for _ in range(200_000)],)),
            ("few-objects", lambda: ([Before() for _ in range(20)],))]
