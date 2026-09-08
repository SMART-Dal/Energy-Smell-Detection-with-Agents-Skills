"""C10.S3 Missing Bulk Primitive Usage -- an append loop against a comprehension."""

def before(xs):
    out = []
    for x in xs:
        out.append(x + 1)
    return out


def after(xs):
    return [x + 1 for x in xs]


def cases():
    return [("large", lambda: (list(range(500_000)),)),
            ("small", lambda: (list(range(50)),))]
