"""C10.S2 -- `map` with a C builtin against a comprehension.

Javad's BuiltInBehavior/ChangeListElementsType says map+builtin wins.
"""

def before(xs):
    return [float(x) for x in xs]


def after(xs):
    return list(map(float, xs))


def cases():
    return [
        ("large", lambda: (list(range(300_000)),)),
        ("small", lambda: (list(range(50)),)),
    ]
