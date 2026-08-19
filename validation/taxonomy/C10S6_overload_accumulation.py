"""C10.S6 Expensive Operator Overloads -- accumulating through `__add__`.

Every `+` on a user type is a dunder lookup, a bound method, a frame and an
allocation for the result; the repair does the arithmetic on primitives and
wraps once at the end. The card warns this is most often wrong for the reason
the class exists -- the invariants it enforces -- so `after` still returns a
`Money`, and only the intermediates are unwrapped.
"""

class Money:
    __slots__ = ("cents",)

    def __init__(self, cents):
        self.cents = cents

    def __add__(self, other):
        return Money(self.cents + other.cents)

    def __eq__(self, other):
        return isinstance(other, Money) and self.cents == other.cents

    def __hash__(self):
        return hash(self.cents)


def before(amounts):
    total = Money(0)
    for amount in amounts:
        total = total + amount
    return total


def after(amounts):
    cents = 0
    for amount in amounts:
        cents += amount.cents
    return Money(cents)


def cases():
    return [("large",  lambda: ([Money(i) for i in range(400_000)],)),
            ("normal", lambda: ([Money(i) for i in range(4_000)],)),
            ("edge",   lambda: ([],))]
