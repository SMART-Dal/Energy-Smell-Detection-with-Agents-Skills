"""C7.S5 Unsimplified Operation -- work that algebra removes.

sum(x * 2 for x) is 2 * sum(x): one multiply instead of n.
"""

def before(xs):
    return sum(x * 2 for x in xs)


def after(xs):
    return 2 * sum(xs)


def cases():
    return [("large", lambda: (list(range(500_000)),)),
            ("small", lambda: (list(range(50)),)),
            ("empty", lambda: ([],))]
