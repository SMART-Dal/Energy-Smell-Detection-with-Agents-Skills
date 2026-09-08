"""C1.S4 Repeated Computation -- the same pure call evaluated twice per item."""

def before(rows):
    out = []
    for r in rows:
        if len(str(r)) > 3:
            out.append(len(str(r)))
    return out


def after(rows):
    out = []
    for r in rows:
        width = len(str(r))
        if width > 3:
            out.append(width)
    return out


def cases():
    return [("large", lambda: (list(range(200_000)),)),
            ("small", lambda: (list(range(50)),))]
