"""Cases for method_ignores_self."""

import abc
import functools


class Report:
    def format_cell(self, value):
        # Never touches `self`.
        return f"{value:>10.2f}"

    def widths(self, rows):
        # Uses `self`, so the binding is doing something.
        return [len(row) + self.padding for row in rows]

    def render(self, rows):
        # `self` appears only inside a nested comprehension, and still counts.
        return [self.format_cell(v) for row in rows for v in row]

    def _slug(self, text):
        # A private helper that ignores `self`: the clearest case.
        return text.strip().lower().replace(" ", "-")

    def __len__(self):
        # A dunder has to keep its signature.
        return 3

    @staticmethod
    def already_static(value):
        # Nothing to report.
        return value * 2

    @property
    def title(self):
        # Decorated, so the signature is fixed by the protocol.
        return "report"


class Base(abc.ABC):
    @abc.abstractmethod
    def load(self, path):
        # An abstract stub ignores `self` by definition.
        ...

    def helper(self, value):
        # A plain stub body, not abstract: still a candidate.
        return value + 1


def module_level(value):
    # Not a method at all.
    return value * 2


class Charge:
    def fee(self, amount):
        # Ignores `self`, but `PremiumCharge` overrides it, so this is the
        # dispatch point: the call-site half of the repair, `Charge.fee(x, a)`,
        # would skip every override.
        return amount * 2


class PremiumCharge(Charge):
    def fee(self, amount):
        return amount


class Saver:
    def save(self):
        # Silent. Zero-argument `super()` compiles using `__class__` and the
        # first positional parameter, so `@staticmethod` here does not change a
        # lookup -- it raises `RuntimeError: super(): no arguments`. The body
        # never names `self`, which is exactly why the rule needed telling.
        return super().save()


class WidgetTest:
    def test_addition(self):
        # Silent. A runner discovers this by name; nothing calls it, so the
        # repair -- make it static and rewrite the call sites -- has no call
        # site to rewrite.
        assert 1 + 1 == 2
