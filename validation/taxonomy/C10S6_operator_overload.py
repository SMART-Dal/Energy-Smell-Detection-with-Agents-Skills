"""C10.S6 Expensive Operator Overloads -- a Python __add__ called per element."""

class Money:
    __slots__ = ("cents",)

    def __init__(self, cents):
        self.cents = cents

    def __add__(self, other):
        return Money(self.cents + other.cents)


def before(items):
    total = Money(0)
    for m in items:
        total = total + m
    return total.cents


def after(items):
    total = 0
    for m in items:
        total += m.cents
    return total


def cases():
    return [("large", lambda: ([Money(i) for i in range(200_000)],)),
            ("small", lambda: ([Money(i) for i in range(20)],)),
            ("empty", lambda: ([],))]
