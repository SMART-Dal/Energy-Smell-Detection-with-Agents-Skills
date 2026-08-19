"""C2.S3 Excessive Modularization -- keep every layer, bypass them in bulk.

The card's second repair example and the shape it says real code usually needs:
nothing that calls `get`, `_raw` or `_decode` breaks, because all three survive;
only the bulk path skips them. The card also warns that the work at the bottom
may dominate, which is why `_decode` here is a cheap dict lookup rather than a
JSON parse -- with a parse the frames disappear into it and the ratio fails,
which is the `heavy-bottom` file's job.
"""

class Store:
    __slots__ = ("_data",)

    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._decode(self._raw(key))

    def _raw(self, key):
        return self._data[key]

    def _decode(self, blob):
        return blob * 2

    def load_all_layered(self, keys):
        return [self.get(k) for k in keys]

    def load_all_direct(self, keys):
        data = self._data
        return [data[k] * 2 for k in keys]


def before(store, keys):
    return store.load_all_layered(keys)


def after(store, keys):
    return store.load_all_direct(keys)


def _store(n):
    return Store({i: i for i in range(n)})


def cases():
    return [("large",  lambda: (_store(300_000), list(range(300_000)))),
            ("normal", lambda: (_store(3_000), list(range(3_000)))),
            ("edge",   lambda: (_store(1), []))]
