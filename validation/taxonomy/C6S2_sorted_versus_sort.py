"""C6.S2 Unnecessary Data Copying -- `sorted()` where `.sort()` would do.

The card says the judgement here is entirely about ownership: the copy was
buying isolation from a caller who must not see the mutation. This file makes
that claim explicitly with `EQUIVALENCE = "returns_only"`, which is exactly the
declaration the harness provides for it -- the answer is the same and only the
side effect differs.
"""

EQUIVALENCE = "returns_only"


def before(values):
    return sorted(values)


def after(values):
    values.sort()
    return values


def _scrambled(n):
    return [(i * 7919) % n for i in range(n)]


def cases():
    return [("large",  lambda: (_scrambled(400_000),)),
            ("normal", lambda: (_scrambled(4_000),))]
