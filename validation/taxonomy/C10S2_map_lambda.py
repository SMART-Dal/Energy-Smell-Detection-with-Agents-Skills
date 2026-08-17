"""C10.S2 -- `map` with a lambda against a comprehension.

Javad's BuiltInBehavior/SumMap2 goes the other way from ChangeListElementsType:
it replaces map+lambda *with* a comprehension. Both cannot be a general rule.
If the deciding factor is whether the mapped callable is a C builtin or a
Python-level lambda, the card has to say so.
"""

def before(xs):
    return sum(map(lambda x: x * 2, xs))


def after(xs):
    return sum([x * 2 for x in xs])


def cases():
    return [
        ("large", lambda: (list(range(300_000)),)),
        ("small", lambda: (list(range(50)),)),
        ("empty", lambda: ([],)),
    ]
