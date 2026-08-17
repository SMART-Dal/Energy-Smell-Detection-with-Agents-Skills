"""C4.S4 Missing Else-If -- independent ifs where the cases are exclusive."""

def before(xs):
    out = 0
    for x in xs:
        r = x % 4
        if r == 0:
            out += 1
        if r == 1:
            out += 2
        if r == 2:
            out += 3
        if r == 3:
            out += 4
    return out


def after(xs):
    out = 0
    for x in xs:
        r = x % 4
        if r == 0:
            out += 1
        elif r == 1:
            out += 2
        elif r == 2:
            out += 3
        else:
            out += 4
    return out


def cases():
    return [("large", lambda: (list(range(500_000)),)),
            ("small", lambda: (list(range(50)),))]
