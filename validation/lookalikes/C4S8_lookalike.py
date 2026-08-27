"""C4.S8 Non-Idiomatic Condition -- LOOKS THE SAME, IS NOT: `if not x` and
`if len(x) == 0` do not ask the same question.

The description gives the swap as its first example -- "using if len(my_list) ==
0 instead of if not my_list" -- and `C4S8_non_idiomatic` measures the idiom
family at +56%. The rewrite is right whenever `x` is known to be a sequence.

`x` here is whatever the caller passed: a list, a string, or a number. `not 0`
is `True` and `len(0)` raises, so the two forms disagree on every zero and on
every empty string that was meant to be a legitimate value. The verbose form was
verbose because it was also asserting a type.

The check is what the name can hold. `if not x` is the idiom for a container
whose type is certain; where `0`, `0.0`, `""` or `False` are meaningful values,
the explicit comparison is the correct code and the idiom is a bug.
"""

def before(values):
    kept = 0
    for value in values:
        if isinstance(value, (list, str)) and len(value) == 0:
            continue
        kept += 1
    return kept


def after(values):
    kept = 0
    for value in values:
        if not value:
            continue
        kept += 1
    return kept


def _values(n, with_zeros):
    out = []
    for i in range(n):
        if with_zeros and i % 5 == 0:
            out.append(0)
        elif i % 3 == 0:
            out.append([])
        else:
            out.append([i])
    return out


def cases():
    return [("has-zeros", lambda: (_values(400_000, True),)),
            ("no-zeros",  lambda: (_values(400_000, False),)),
            ("edge",      lambda: ([],))]
