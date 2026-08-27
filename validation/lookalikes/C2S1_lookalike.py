"""C2.S1 Unnecessary Method Delegation -- LOOKS THE SAME, IS NOT: the property is doing
the work the attribute cannot.

`C2S1_property_per_element` measures the real thing at +43.2%: a `@property`
that returns `self._key` unchanged, bypassed at the hot call site. The shape
here is identical from the outside -- a property, a private attribute behind it,
and a loop reading it once per element.

`size` computes on first access and stores the result. Reading `_size` directly
gets `None` until something has read `size` at least once, so the bypass does
not remove an indirection, it removes the only code that ever fills the field.

The distinction is one line of the property body: a `return self._x` may be
bypassed, anything else may not.
"""

class Report:
    __slots__ = ("_rows", "_size")

    def __init__(self, rows):
        self._rows = rows
        self._size = None

    @property
    def size(self):
        if self._size is None:
            self._size = len(self._rows)
        return self._size


def before(reports):
    return sum(report.size for report in reports)


def after(reports):
    return sum(report._size for report in reports)


def _reports(count, width):
    return [Report(list(range(width))) for _ in range(count)]


def cases():
    return [("many-reports", lambda: (_reports(200_000, 4),)),
            ("few-reports",  lambda: (_reports(200, 4),)),
            ("edge",         lambda: ([],))]
