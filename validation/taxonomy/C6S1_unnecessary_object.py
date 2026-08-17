"""C6.S1 Unnecessary Object -- dict() call where a literal would do."""

def before(n):
    out = []
    for i in range(n):
        out.append(dict(a=i, b=i + 1))
    return len(out)


def after(n):
    out = []
    for i in range(n):
        out.append({"a": i, "b": i + 1})
    return len(out)


def cases():
    return [("large", lambda: (300_000,)), ("small", lambda: (20,))]
