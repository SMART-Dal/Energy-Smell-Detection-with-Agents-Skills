"""C4.S7 Missing Edge-Case Guards -- no early return for the trivial input."""

def before(xs, ys):
    result = []
    for x in xs:
        for y in ys:
            result.append(x * y)
    return result


def after(xs, ys):
    if not xs or not ys:
        return []
    result = []
    for x in xs:
        for y in ys:
            result.append(x * y)
    return result


def cases():
    return [("trivial-input", lambda: (list(range(200_000)), [])),
            ("real-input", lambda: (list(range(400)), list(range(400))))]
