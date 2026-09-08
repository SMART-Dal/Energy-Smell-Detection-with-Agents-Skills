"""C2.S1 Unnecessary Method Delegation -- name-mangled accessors called from
other methods of the same class.

The card's first repair example, and the reason it is available: the accessors
are private, so nothing outside the class can be calling them and deleting them
is safe. Two frames per iteration disappear. This is the same root cause as the
property case with a different shape of wrapper.
"""

class BeforeUser:
    __slots__ = ("_name",)

    def __init__(self, name):
        self._name = name

    def __get_name(self):
        return self._name

    def print_name(self):
        return f"The name is {self.__get_name()}"


class AfterUser:
    __slots__ = ("_name",)

    def __init__(self, name):
        self._name = name

    def print_name(self):
        return f"The name is {self._name}"


def before(name, repeats):
    user = BeforeUser(name)
    total = 0
    for _ in range(repeats):
        total += len(user.print_name())
    return total


def after(name, repeats):
    user = AfterUser(name)
    total = 0
    for _ in range(repeats):
        total += len(user.print_name())
    return total


def cases():
    return [("many-calls", lambda: ("ada", 1_000_000)),
            ("few-calls",  lambda: ("ada", 100))]
