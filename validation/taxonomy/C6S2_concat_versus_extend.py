"""C6.S2 Unnecessary Data Copying -- `out = out + group` in an accumulation.

`out + group` builds a new list holding everything accumulated so far, so the
total copying is quadratic in the output length; `extend` grows the existing
buffer. This is the largest form of the root cause and the one where the copy
buys nothing at all -- nothing else refers to `out`.
"""

def before(groups):
    out = []
    for group in groups:
        out = out + group
    return len(out)


def after(groups):
    out = []
    for group in groups:
        out.extend(group)
    return len(out)


def cases():
    return [("many-groups", lambda: ([[1, 2, 3, 4]] * 20_000,)),
            ("few-groups",  lambda: ([[1, 2, 3, 4]] * 50,)),
            ("edge",        lambda: ([],))]
