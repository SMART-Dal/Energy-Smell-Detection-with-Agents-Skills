"""C12.S3 Unpredictable Branches -- a data-dependent branch in a tight loop.

The card claims branchless arithmetic wins when the branch cannot be predicted.
In CPython the interpreter overhead may swamp the effect entirely, which is
itself the finding: the claim may be true of C and false of Python.
"""

def before(xs):
    total = 0
    for x in xs:
        if x > 0:
            total += x
    return total


def after(xs):
    total = 0
    for x in xs:
        total += x * (x > 0)
    return total


def cases():
    return [("unpredictable", lambda: ([(i * 7919) % 2001 - 1000 for i in range(300_000)],)),
            ("predictable", lambda: (list(range(300_000)),))]
