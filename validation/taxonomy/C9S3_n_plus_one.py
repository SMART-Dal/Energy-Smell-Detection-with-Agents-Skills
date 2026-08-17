"""C9.S3 Inefficient Retrieval Paths -- one lookup per row against one batched.

A dict stands in for the store; the per-call cost is the point, not the medium.
"""

class Store:
    def __init__(self, data):
        self.data = data

    def fetch_one(self, key):
        return self.data.get(key)

    def fetch_many(self, keys):
        return {k: self.data.get(k) for k in keys}


def before(store, keys):
    return [store.fetch_one(k) for k in keys]


def after(store, keys):
    found = store.fetch_many(keys)
    return [found[k] for k in keys]


def cases():
    data = {i: i * 2 for i in range(50_000)}
    return [("many-rows", lambda: (Store(dict(data)), list(range(50_000)))),
            ("one-row", lambda: (Store(dict(data)), [1]))]
