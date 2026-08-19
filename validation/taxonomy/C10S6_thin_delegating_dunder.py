"""C10.S6 Expensive Operator Overloads -- a dunder that is a thin delegation.

The card's second `NOT a smell when` clause: when the operation is already
delegated to compiled code, the dunder is a wrapper over a C operation and the
cost is the call rather than the body. Same repair as the accumulation case,
and the difference between the two readings is what the *body* was
contributing.
"""

import numpy as np


class Vector:
    __slots__ = ("data",)

    def __init__(self, data):
        self.data = data

    def __add__(self, other):
        return Vector(self.data + other.data)      # numpy does the work

    def __eq__(self, other):
        return isinstance(other, Vector) and bool(np.array_equal(self.data, other.data))


def before(vectors, width):
    total = Vector(np.zeros(width))
    for vector in vectors:
        total = total + vector
    return total


def after(vectors, width):
    acc = np.zeros(width)
    for vector in vectors:
        acc = acc + vector.data
    return Vector(acc)


def _vectors(n, width):
    return [Vector(np.full(width, 1.0)) for _ in range(n)], width


def cases():
    return [("many-small", lambda: _vectors(200_000, 4)),
            ("few-large",  lambda: _vectors(2_000, 4_000)),
            ("edge",       lambda: ([], 4))]
