"""C2.S3 Excessive Modularization -- the same chain, with real work at the
bottom.

This is the adversarial half of C2.S3 and the card's stated precondition: the
finding is a *ratio*, not a count of layers. Three frames around a JSON parse
should disappear into the parse, so the expected reading is close to nothing --
and if it is, the card can say how thin "thin" has to be.

Deliberately identical in structure to `C2S3_bypass_on_bulk_path`; only the
work at the bottom differs.
"""

import json


class Store:
    __slots__ = ("_data",)

    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._decode(self._raw(key))

    def _raw(self, key):
        return self._data[key]

    def _decode(self, blob):
        return json.loads(blob)

    def load_all_layered(self, keys):
        return [self.get(k) for k in keys]

    def load_all_direct(self, keys):
        data, decode = self._data, json.loads
        return [decode(data[k]) for k in keys]


def before(store, keys):
    return store.load_all_layered(keys)


def after(store, keys):
    return store.load_all_direct(keys)


def _store(n):
    payload = json.dumps({"a": 1, "b": [1, 2, 3], "c": "text"})
    return Store({i: payload for i in range(n)})


def cases():
    return [("large",  lambda: (_store(60_000), list(range(60_000)))),
            ("normal", lambda: (_store(1_000), list(range(1_000)))),
            ("edge",   lambda: (_store(1), []))]
