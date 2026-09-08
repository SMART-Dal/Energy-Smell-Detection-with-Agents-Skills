"""C4.S6 Expensive Exception Control Flow -- raising on the common path.

The two cases decide the card: exceptions are cheap when rare and ruinous when
frequent, so `always-raises` and `never-raises` must be reported together.
"""

def before(keys, table):
    out = []
    for k in keys:
        try:
            out.append(table[k])
        except KeyError:
            out.append(0)
    return out


def after(keys, table):
    out = []
    for k in keys:
        if k in table:
            out.append(table[k])
        else:
            out.append(0)
    return out


def cases():
    table = {i: i for i in range(1000)}
    return [("always-raises", lambda: (list(range(10_000, 210_000)), dict(table))),
            ("never-raises", lambda: ([i % 1000 for i in range(200_000)], dict(table)))]
