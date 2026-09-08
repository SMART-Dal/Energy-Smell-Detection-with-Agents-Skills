"""C6.S1 Unnecessary Object Creation -- `dict()` where `{}` would do.

The card says this is real and small -- a global lookup plus a call plus
keyword packing against a single bytecode -- and honestly advisory on anything
but a very hot path. This is where that gets a number, so the card can say how
hot "very hot" is.
"""

def before(n):
    out = []
    for i in range(n):
        out.append(dict(host="localhost", port=i))
    return len(out)


def after(n):
    out = []
    for i in range(n):
        out.append({"host": "localhost", "port": i})
    return len(out)


def cases():
    return [("many",   lambda: (1_000_000,)),
            ("normal", lambda: (10_000,))]
