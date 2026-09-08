"""C2.S1 Unnecessary Method Delegation -- a `@property` that returns a stored
attribute, read once per element.

The card says attribute access through a property runs the descriptor protocol
where a plain read is a dict lookup, and that the right repair is usually to
bypass it at the hot call site rather than to delete it -- so `after` keeps the
property and reads `_key` directly in the one comprehension that is hot.
"""

class Row:
    __slots__ = ("_key",)

    def __init__(self, key):
        self._key = key

    @property
    def key(self):
        return self._key


def before(rows):
    # `len` of the index rather than the index itself: the work being measured
    # is building it, and returning it would compare `Row` objects by identity,
    # which differ between the two calls because the thunk makes them fresh.
    return len({row.key: row for row in rows})


def after(rows):
    return len({row._key: row for row in rows})


def cases():
    return [("large",  lambda: ([Row(i) for i in range(300_000)],)),
            ("normal", lambda: ([Row(i) for i in range(3_000)],))]
