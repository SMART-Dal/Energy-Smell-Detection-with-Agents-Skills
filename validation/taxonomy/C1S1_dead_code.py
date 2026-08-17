"""C1.S1 Dead Code -- a value computed into a local nothing reads."""

def before(xs):
    total = 0
    for x in xs:
        scratch = sorted(str(x))          # never read
        total += x
    return total


def after(xs):
    total = 0
    for x in xs:
        total += x
    return total


def cases():
    return [("large", lambda: (list(range(200_000)),)),
            ("small", lambda: (list(range(50)),)),
            ("empty", lambda: ([],))]
