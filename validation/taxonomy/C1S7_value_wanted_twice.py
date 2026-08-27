"""C1.S7 Unnecessary Variable -- the single-use temporary is
used twice once you inline it.

`width = len(str(record)); return width` is the canonical case and inlining it
saves two bytecodes. It reads as the same shape here: `width` is assigned, and
the next line is the only place the name appears.

The name appears once. The *value* is wanted twice -- in the test and in the
result -- so inlining it duplicates the call that produced it. What looks like
removing a binding is adding a `str()` and a `len()` per surviving element, and
this is the exact inverse of `C1S4_repeated_computation`, which measures the
same code in the other direction at +42.4%.

Count uses of the value, not occurrences of the name.
"""

def before(records, floor):
    out = []
    for record in records:
        width = len(str(record))
        if width > floor:
            out.append(width)
    return out


def after(records, floor):
    out = []
    for record in records:
        if len(str(record)) > floor:
            out.append(len(str(record)))
    return out


def cases():
    return [("mostly-kept",     lambda: (list(range(200_000)), 3)),
            ("mostly-rejected", lambda: (list(range(200_000)), 99)),
            ("edge",            lambda: ([], 1))]
