"""C2.S2 Missing Static Declaration -- LOOKS THE SAME, IS NOT: the method ignores
`self` in this class and not in the next one.

"Never references self" is the whole test, and it is true of `Base.fee` here.
`C2S2_declaration_only` makes the same edit and reads -5.2%, so the saving was
already doubtful; this is the case where the edit is wrong rather than small.

`@staticmethod` is harmless on its own. What the repair usually comes with is
the call site changing from `self.fee(...)` to `Base.fee(...)` to skip the
binding, and that hard-codes the class. `Premium` overrides `fee`, so every
premium account is charged the base rate.

Before declaring a method static, look for overrides. A method that ignores
`self` in the class where it is defined may still be the polymorphic entry
point.
"""

class Base:
    __slots__ = ("balance",)

    def __init__(self, balance):
        self.balance = balance

    def fee(self, amount):               # never touches self
        return amount * 2


class Premium(Base):
    __slots__ = ()

    def fee(self, amount):
        return amount


def before(accounts, amount):
    return sum(account.fee(amount) for account in accounts)


def after(accounts, amount):
    return sum(Base.fee(account, amount) for account in accounts)


def _accounts(n, premium_ratio):
    if not premium_ratio:
        return [Base(i) for i in range(n)]
    step = max(1, int(1 / premium_ratio))
    return [Premium(i) if i % step == 0 else Base(i) for i in range(n)]


def cases():
    return [("some-premium", lambda: (_accounts(300_000, 0.1), 3)),
            ("none-premium", lambda: (_accounts(300_000, 0.0), 3)),
            ("edge",         lambda: ([], 3))]
