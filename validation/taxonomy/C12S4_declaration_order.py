"""C12.S4 Inefficient Array Declaration Order -- the same fields, declared in a different order.

The previous version of this file was broken: `cases()` built a list of
`Before` instances and handed the same list to both variants, so `After` was
never instantiated and the two functions were byte-for-byte identical. It read
+0.6%, which was the measurement of nothing.

Fixed, it asks the question the card needs answered. In a language with struct
layout, declaration order decides addresses. In CPython a `__slots__` entry is a
pointer into the object header and the values live wherever the allocator put
them, so two slots declared next to each other are not adjacent in memory and
reordering them cannot change locality. Both instance arrays are now built at
import, outside every window, and each variant walks its own.

A reading near zero is the card being right to mark this advisory for pure
Python and to send the reader to `C12S4_ctypes_cold_before_hot` for the case
where a layout really is declared.
"""

COUNT = 400_000


class ColdFirst:
    __slots__ = ("error_log", "retry_count", "audit_trail", "value")

    def __init__(self, value):
        self.error_log = None
        self.retry_count = 0
        self.audit_trail = None
        self.value = value


class HotFirst:
    __slots__ = ("value", "error_log", "retry_count", "audit_trail")

    def __init__(self, value):
        self.value = value
        self.error_log = None
        self.retry_count = 0
        self.audit_trail = None


_COLD_FIRST = [ColdFirst(i) for i in range(COUNT)]
_HOT_FIRST = [HotFirst(i) for i in range(COUNT)]


def before(count):
    total = 0
    for row in _COLD_FIRST[:count]:
        total += row.value
    return total


def after(count):
    total = 0
    for row in _HOT_FIRST[:count]:
        total += row.value
    return total


def cases():
    return [("many-objects", lambda: (COUNT,)),
            ("few-objects",  lambda: (200,)),
            ("edge",         lambda: (0,))]
