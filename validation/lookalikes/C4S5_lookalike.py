"""C4.S5 Expensive Comparison -- LOOKS THE SAME, IS NOT: `type(x) is T` is not
`isinstance(x, T)`.

The description offers the swap directly -- "using str(type(x)) string
comparison instead of isinstance(x, TargetType)" -- and `C4S5_heterogeneous_
input` measures the identity form at +31.1%, because it skips the MRO walk.

It skips the subclasses too. `bool` is a subclass of `int` in Python, so every
`True` and `False` in this input is an integer to `isinstance` and is neither
`int` nor `bool`-handled by `type(x) is int`. The identity check drops them into
the fallback arm, and the total is wrong by however many booleans the data
contains.

`type(x) is T` is only interchangeable when no subclass of `T` can reach the
check. `bool`/`int` is the case that catches people, because the data usually
has no booleans in it until the day it does.
"""

def before(values):
    total = 0
    for value in values:
        if isinstance(value, int):
            total += value
        elif isinstance(value, str):
            total += len(value)
    return total


def after(values):
    total = 0
    for value in values:
        kind = type(value)
        if kind is int:
            total += value
        elif kind is str:
            total += len(value)
    return total


def _mixed(n, with_bools):
    out = []
    for i in range(n):
        if with_bools and i % 7 == 0:
            out.append(i % 2 == 0)
        elif i % 3:
            out.append(i)
        else:
            out.append(f"s{i}")
    return out


def cases():
    return [("has-booleans", lambda: (_mixed(300_000, True),)),
            ("no-booleans",  lambda: (_mixed(300_000, False),))]
