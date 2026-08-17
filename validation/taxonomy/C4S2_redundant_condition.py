"""C4.S2 Redundant Conditional Evaluation -- advisory; a test already known."""

def before(xs, k):
    out = []
    for x in xs:
        if x > k:
            if x > k:              # already established
                out.append(x)
    return out


def after(xs, k):
    out = []
    for x in xs:
        if x > k:
            out.append(x)
    return out


def cases():
    return [("large", lambda: (list(range(500_000)), 250_000)),
            ("small", lambda: (list(range(50)), 25))]
