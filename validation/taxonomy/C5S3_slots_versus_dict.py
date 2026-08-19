"""C5.S3 Over-Provisioned Data Type -- an instance with a `__dict__` against
one with `__slots__`.

The description names this directly: heavyweight class instances for simple
records where a namedtuple or `__slots__` would do. An instance with a
`__dict__` is two heap objects and a dict probe per attribute read; slots are
one object and an array index. The card says the effect tracks the number of
instances, so the two cases vary that.
"""

class Plain:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Slotted:
    __slots__ = ("key", "value")

    def __init__(self, key, value):
        self.key = key
        self.value = value


def before(n):
    rows = [Plain(i, i * 2) for i in range(n)]
    return sum(r.key + r.value for r in rows)


def after(n):
    rows = [Slotted(i, i * 2) for i in range(n)]
    return sum(r.key + r.value for r in rows)


def cases():
    return [("many-instances", lambda: (400_000,)),
            ("few-instances",  lambda: (400,)),
            ("edge",           lambda: (0,))]
