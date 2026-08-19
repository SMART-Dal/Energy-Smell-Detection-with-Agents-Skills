"""C8.S4 Redundant External Fetching -- the fetch is already cached a layer
down.

The card's last check: an ORM identity map, an HTTP cache header or the
operating system's page cache may mean no round trip is happening, and the
saving is much smaller than the shape suggests. Here the "store" memoises
internally, so the outer cache is a second dict in front of a dict -- and the
expected reading is close to nothing, which is the answer that stops an agent
adding a cache in front of a cache.
"""

class Store:
    __slots__ = ("_data", "_memo", "fetches")

    def __init__(self, data):
        self._data = data
        self._memo = {}
        self.fetches = 0

    def get(self, key):
        if key not in self._memo:
            self.fetches += 1
            self._memo[key] = self._data[key] * 2
        return self._memo[key]


def before(store, keys):
    total = 0
    for key in keys:
        total += store.get(key)
    return total


def after(store, keys):
    local = {}
    total = 0
    for key in keys:
        if key not in local:
            local[key] = store.get(key)
        total += local[key]
    return total


def _store(n):
    return Store({i: i for i in range(n)})


def cases():
    return [("many-repeats", lambda: (_store(400), [i % 400 for i in range(200_000)])),
            ("all-distinct", lambda: (_store(200_000), list(range(200_000)))),
            ("edge",         lambda: (_store(1), []))]
