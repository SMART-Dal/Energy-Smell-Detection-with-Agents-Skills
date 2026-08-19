"""C4.S5 Expensive Comparison -- a type check per element against dispatch.

The previous version of this file measured `sorted(a) == sorted(b)` against
`Counter(a) == Counter(b)`, which is a different claim entirely and one this
card does not make; it lost by 1222%, correctly, and said nothing about C4.S5.
(That reading is now a near-miss on C10.S2, where it belongs.)

What C4.S5 is about is runtime type introspection on the per-element path.
`isinstance` walks the MRO on every element; moving the per-type arithmetic
onto the classes replaces the chain with one attribute lookup and a bound call.

The card's *other* repair -- hoisting the decision with `all(isinstance(...))`
-- is deliberately not measured here, because it pays a full extra pass and the
card already says it only wins when the loop body is heavier than a comparison.
Measuring the two repairs in one file would attribute the result to whichever
happened to dominate.
"""


class Circle:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2


class Square:
    __slots__ = ("side",)

    def __init__(self, side):
        self.side = side

    def area(self):
        return self.side ** 2


class Triangle:
    __slots__ = ("base", "height")

    def __init__(self, base, height):
        self.base = base
        self.height = height

    def area(self):
        return 0.5 * self.base * self.height


def before(shapes):
    total = 0.0
    for shape in shapes:
        if isinstance(shape, Circle):
            total += 3.14159 * shape.radius ** 2
        elif isinstance(shape, Square):
            total += shape.side ** 2
        elif isinstance(shape, Triangle):
            total += 0.5 * shape.base * shape.height
    return total


def after(shapes):
    total = 0.0
    for shape in shapes:
        total += shape.area()
    return total


def _mixed(n):
    """A realistic mix, with the last-tested type common enough to matter.

    A collection that is all `Circle` would settle every check on the first
    `isinstance` and understate the chain; one that is all `Triangle` would
    walk all three every time and overstate it.
    """
    out = []
    for i in range(n):
        if i % 3 == 0:
            out.append(Circle(i % 7 + 1))
        elif i % 3 == 1:
            out.append(Square(i % 5 + 1))
        else:
            out.append(Triangle(i % 4 + 1, i % 6 + 1))
    return out


def cases():
    return [
        ("large", lambda: (_mixed(200_000),)),
        ("small", lambda: (_mixed(40),)),
        ("empty", lambda: ([],)),
    ]
