"""C4.S8 Non-Idiomatic Condition -- `in dict.keys()` instead of `in dict`."""

def before(keys, table):
    return sum(1 for k in keys if k in table.keys())


def after(keys, table):
    return sum(1 for k in keys if k in table)


def cases():
    table = {i: i for i in range(1000)}
    return [("large", lambda: (list(range(300_000)), dict(table))),
            ("small", lambda: (list(range(50)), dict(table)))]
