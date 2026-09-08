"""C10.S6 Expensive Operator Overloads -- LOOKS THE SAME, IS NOT: the dunder is where
the invariant lives.

"Doing the arithmetic on primitives and wrapping once at the end" is the repair,
and `C10S6_overload_accumulation` measures it at +79.2%: a dunder lookup, a
bound method, a frame and an allocation per element, replaced by an integer add.

`Money.__add__` also refuses to add euros to dollars. Unwrapping to `.cents` and
summing skips the check, so a mixed batch produces a total in no currency at all
and the function returns it as if it were dollars. The overload was not
decoration; it was the only place the rule was enforced.

Read the dunder before removing calls to it. One that forwards to a primitive or
to a compiled library may be bypassed on the hot path; one that validates,
normalises units, rounds, or raises is doing something the loop then has to do
itself -- and doing it inline usually costs what the dispatch did.
"""

class Money:
    __slots__ = ("cents", "currency")

    def __init__(self, cents, currency="usd"):
        self.cents = cents
        self.currency = currency

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError(f"{self.currency} + {other.currency}")
        return Money(self.cents + other.cents, self.currency)

    def __eq__(self, other):
        return (isinstance(other, Money) and self.cents == other.cents
                and self.currency == other.currency)

    def __hash__(self):
        return hash((self.cents, self.currency))


def before(amounts):
    total = Money(0, amounts[0].currency if amounts else "usd")
    for amount in amounts:
        total = total + amount
    return total


def after(amounts):
    cents = 0
    for amount in amounts:
        cents += amount.cents                 # the currency check is gone
    return Money(cents, amounts[0].currency if amounts else "usd")


def _amounts(n, mixed):
    if not mixed:
        return [Money(i, "usd") for i in range(n)]
    return [Money(i, "eur" if i % 10_000 == 9_999 else "usd") for i in range(n)]


def cases():
    return [("mixed-currencies", lambda: (_amounts(300_000, True),)),
            ("one-currency",     lambda: (_amounts(300_000, False),))]
