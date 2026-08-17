"""C3.S1 Inefficient Iteration Construct -- indexing by range(len(x)).

From Javad's BuiltInBehavior/TraverseList.
"""

def before(xs):
    return [xs[i] * 2 for i in range(len(xs))]


def after(xs):
    return [x * 2 for x in xs]


def cases():
    return [("large", lambda: (list(range(400_000)),)),
            ("small", lambda: (list(range(50)),)),
            ("empty", lambda: ([],))]
