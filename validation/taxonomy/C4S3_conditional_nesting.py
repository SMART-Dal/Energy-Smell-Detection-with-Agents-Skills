"""C4.S3 Inefficient Conditional Nesting -- advisory; deep nesting vs guards."""

def before(xs, k):
    out = 0
    for x in xs:
        if x is not None:
            if x > 0:
                if x > k:
                    out += x
    return out


def after(xs, k):
    out = 0
    for x in xs:
        if x is None:
            continue
        if x <= 0:
            continue
        if x <= k:
            continue
        out += x
    return out


def cases():
    return [("large", lambda: (list(range(500_000)), 250_000)),
            ("small", lambda: (list(range(50)), 25))]
