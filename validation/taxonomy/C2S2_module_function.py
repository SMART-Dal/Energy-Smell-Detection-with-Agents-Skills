"""C2.S2 Missing Static Declaration -- moved out of the class entirely.

The card's second repair example and the larger of the two: a module-level
function skips the class namespace lookup as well as the binding, at the cost
of every call site inside the class losing its `self.`. If this pays where the
decorator alone does not, the card should say to prefer this form on a hot
path.
"""

def _split_fields(line):
    return [f.strip() for f in line.split(",")]


class Before:
    __slots__ = ()

    def _split_fields(self, line):
        return [f.strip() for f in line.split(",")]

    def parse(self, lines):
        return [self._split_fields(line) for line in lines]


class After:
    __slots__ = ()

    def parse(self, lines):
        return [_split_fields(line) for line in lines]


def before(lines):
    return Before().parse(lines)


def after(lines):
    return After().parse(lines)


def cases():
    return [("large",  lambda: ([f"a{i}, b{i} , c{i}" for i in range(200_000)],)),
            ("normal", lambda: ([f"a{i}, b{i} , c{i}" for i in range(2_000)],))]
