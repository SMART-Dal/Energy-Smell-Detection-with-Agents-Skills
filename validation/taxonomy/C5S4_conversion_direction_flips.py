"""C5.S4 Unnecessary Representation Change -- the same edit, opposite verdicts.

The card's headline near-miss, from two of the project's own samples.
`set.intersection` iterates its argument and probes the receiver, so a list
argument costs nothing and the inner `set()` is pure overhead;
`set.difference` benefits from a hashed argument. The *edit* is identical --
delete an inner `set()` -- and only the receiving method differs.

Here `before` keeps the conversion and `after` deletes it, on `intersection`
where deleting it should pay, and on `difference` where it should not. Two
cases, one file, and the gap between them is the whole lesson.
"""

def before(a, b, method):
    if method == "intersection":
        return len(set(a).intersection(set(b)))
    return len(set(a).difference(set(b)))


def after(a, b, method):
    if method == "intersection":
        return len(set(a).intersection(b))
    return len(set(a).difference(b))


def _lists(n):
    return [i for i in range(n)], [i for i in range(n // 2, n + n // 2)]


def cases():
    a, b = _lists(400_000)
    return [("intersection", lambda: (a, b, "intersection")),
            ("difference",   lambda: (a, b, "difference"))]
