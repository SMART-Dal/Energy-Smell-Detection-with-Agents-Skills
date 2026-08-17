"""C9.S4 Expensive Query Pattern -- filtering after retrieval instead of before."""

class Store:
    def __init__(self, rows):
        self.rows = rows

    def all_rows(self):
        return list(self.rows)

    def where(self, predicate):
        return [r for r in self.rows if predicate(r)]


def before(store, k):
    return [r for r in store.all_rows() if r > k]


def after(store, k):
    return store.where(lambda r: r > k)


def cases():
    rows = list(range(200_000))
    return [("selective", lambda: (Store(list(rows)), 199_000)),
            ("unselective", lambda: (Store(list(rows)), -1))]
