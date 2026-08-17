"""C4.S5 Expensive Comparison -- building objects to answer a yes/no question.

Also the measured test of the `expensive_comparison` analyzer added this pass.
"""

def before(pairs):
    return sum(1 for a, b in pairs if sorted(a) == sorted(b))


def after(pairs):
    from collections import Counter
    return sum(1 for a, b in pairs if Counter(a) == Counter(b))


def cases():
    return [("large", lambda: ([([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])] * 100_000,)),
            ("small", lambda: ([([1, 2], [2, 1])] * 20,)),
            ("empty", lambda: ([],))]
