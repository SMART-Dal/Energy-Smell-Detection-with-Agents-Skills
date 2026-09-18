"""C10.S3 Element-wise Operation Over Bulk Primitive -- a slice, not an index loop.

The comprehension builds a `range`, boxes every index and does a bounds-checked
subscript per element. The slice computes the result size once and copies
pointers in C.

The behaviour difference is what the card has to warn about and what no other
measured file in this root cause exercises: a slice returns the input's own
type, where the comprehension always returns a list. `tuple-input` is here to
make that visible -- the two variants return different types for it, so the
case file declares the comparison it wants rather than pretending they match.
"""

def equivalent(before_result, after_result):
    """Compare element by element rather than by container type.

    A slice of a tuple is a tuple; the comprehension always returns a list. The
    two hold the same elements in the same order and differ only in type, which
    is precisely the behaviour change the card warns about. Comparing on values
    states that difference instead of hiding it -- and still fails a repair that
    returns the wrong elements, or the right ones in the wrong order.
    """
    return list(before_result) == list(after_result)


def before(values):
    return [values[i] for i in range(0, len(values), 2)]


def after(values):
    return values[::2]


def cases():
    return [("list-input",  lambda: (list(range(600_000)),)),
            ("tuple-input", lambda: (tuple(range(600_000)),))]
