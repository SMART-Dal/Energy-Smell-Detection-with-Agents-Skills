"""C5.S4 Unnecessary Representation Change -- LOOKS THE SAME, IS NOT: the generator is
consumed twice.

"Converting a generator to a list only to iterate over it once" is the
description's first example, and the `list()` call here is exactly that shape:
wrapped around a comprehension, handed straight to a consumer.

It is handed to two consumers. A generator is exhausted by the first, so the
second sees nothing: the total is right and the count is zero, and the function
returns a ratio that is silently wrong rather than raising.

The clause is "consumed exactly once". That is a fact about the call sites
below the conversion, not about the conversion, and the two-pass case is easy to
miss because the second pass is often a `len`, a `max` or a second `sum` several
lines away.
"""

def _sizes(rows):
    return (len(row) for row in rows)


def before(rows):
    sizes = list(_sizes(rows))
    total = sum(sizes)
    count = sum(1 for _ in sizes)
    return total, count


def after(rows):
    sizes = _sizes(rows)
    total = sum(sizes)
    count = sum(1 for _ in sizes)
    return total, count


def cases():
    return [("many-rows", lambda: ([list(range(i % 8)) for i in range(300_000)],)),
            ("few-rows",  lambda: ([list(range(i % 8)) for i in range(300)],))]
