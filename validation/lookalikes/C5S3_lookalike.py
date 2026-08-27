"""C5.S3 Over-Provisioned Data Type -- LOOKS THE SAME, IS NOT: `__slots__` removes the
thing the rest of the code was using.

"Creating full class instances with __dict__ overhead when __slots__ ... would
work" is the description, and `C5S3_slots_versus_dict` measures the swap at
+38.2%. Two heap objects become one and a dict probe becomes an array index.

The clause is "would work". `__slots__` also removes `__dict__`, and the
enrichment pass here attaches a field that was not declared, which is exactly
what a plain instance is for. Under slots it raises `AttributeError` on the
first row.

Before narrowing an instance, look for every attribute anyone ever sets on it --
including the ones set from other modules, from `setattr`, and from
deserialisation. The declaration has to list all of them, and a class whose
fields are genuinely open cannot be narrowed at all.
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


def _enrich(rows, tag):
    for row in rows:
        row.tag = tag                      # not declared anywhere
    return sum(r.value for r in rows if r.tag == tag)


def before(count, tag):
    return _enrich([Plain(i, i * 2) for i in range(count)], tag)


def after(count, tag):
    return _enrich([Slotted(i, i * 2) for i in range(count)], tag)


def cases():
    return [("many-instances", lambda: (300_000, 1)),
            ("few-instances",  lambda: (300, 1)),
            ("edge",           lambda: (0, 1))]
