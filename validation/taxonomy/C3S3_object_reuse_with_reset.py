"""C3.S3 Per-Iteration Object Creation -- one instance reset instead of N built.

The third repair the card teaches, and the one with a precondition the other
two do not have: the instance must not escape the iteration that filled it.
Here each is rendered to a string immediately, which is what makes reuse
available -- collecting the objects themselves would make every entry the same
object and the repair a bug.

Also the measured example behind C6.S1's first repair, which is the same edit
described as object creation rather than as per-iteration setup.
"""


class Person:
    __slots__ = ("name", "age")

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        return f"{self.name} ({self.age})"


def before(count):
    out = []
    for i in range(count):
        person = Person(f"person {i}", i)
        out.append(str(person))
    return out


def after(count):
    out = []
    person = Person("", 0)
    for i in range(count):
        person.name = f"person {i}"
        person.age = i
        out.append(str(person))
    return out


def cases():
    return [("many",   lambda: (300_000,)),
            ("normal", lambda: (3_000,))]
