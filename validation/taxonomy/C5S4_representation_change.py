"""C5.S4 Unnecessary Representation Change -- a cast that changes nothing.

From Javad's BuiltInBehavior/ReverseList and the ruff C4xx family.
"""

def before(xs):
    return sum(list([x * 2 for x in xs]))


def after(xs):
    return sum([x * 2 for x in xs])


def cases():
    return [("large", lambda: (list(range(400_000)),)),
            ("small", lambda: (list(range(50)),))]
