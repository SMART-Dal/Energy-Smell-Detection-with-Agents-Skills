"""C2.S1 Unnecessary Method Delegation -- a wrapper that only forwards."""

class Store:
    def __init__(self, data):
        self.data = data

    def _lookup(self, k):
        return self.data.get(k, 0)

    def get(self, k):
        return self._lookup(k)


def before(store, keys):
    return sum(store.get(k) for k in keys)


def after(store, keys):
    return sum(store._lookup(k) for k in keys)


def cases():
    data = {i: i for i in range(1000)}
    return [("many-calls", lambda: (Store(dict(data)), list(range(200_000)))),
            ("few-calls", lambda: (Store(dict(data)), list(range(50))))]
