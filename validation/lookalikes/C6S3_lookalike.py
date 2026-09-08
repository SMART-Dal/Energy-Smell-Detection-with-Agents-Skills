"""C6.S3 Unnecessary Data Materialization -- LOOKS THE SAME, IS NOT: the consumer needs
a length.

"Avoid calling list() on generators before passing to functions that accept
iterables" is the description, and `C6S3_genexp_to_list` measures the trade in
both directions. A generator that is reduced once really does save the
allocation.

The consumer here reduces it and then asks how many elements there were. A
generator has no length, so the mechanical repair either raises `TypeError` or
-- as written, which is what an agent producing "equivalent" code does -- runs a
second pass that finds the generator exhausted and reports zero.

The clause is "when the result is consumed exactly once". `len()`, `max()` after
`sum()`, indexing, slicing, membership tests and a second loop all count as a
second consumption, and none of them look like one at the call site.
"""

def _weights(rows):
    return (row * 3 + 1 for row in rows)


def before(rows):
    weights = list(_weights(rows))
    return sum(weights), len(weights)


def after(rows):
    weights = _weights(rows)
    return sum(weights), sum(1 for _ in weights)


def cases():
    return [("many-rows", lambda: (list(range(400_000)),)),
            ("few-rows",  lambda: (list(range(400)),))]
