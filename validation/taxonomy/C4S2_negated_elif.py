"""C4.S2 Determined Condition -- an `elif` restating the negation of its `if`.

The commonest shape this root cause takes. Reaching the `elif` means `x < 0`
was false, so `x >= 0` is already known and the comparison cannot fail.

It also carries the behaviour trap the card warns about: the original returns
`None` for a NaN input, because neither arm matches, and the repair returns the
NaN. The cases below are finite, so the two agree on everything measured -- the
trap is real and is the reason the card tells a reader to check for it rather
than apply the edit from the shape alone.
"""


def _relu_before(x):
    if x < 0:
        return 0
    elif x >= 0:
        return x


def _relu_after(x):
    if x < 0:
        return 0
    return x


def before(values):
    return sum(_relu_before(v) for v in values)


def after(values):
    return sum(_relu_after(v) for v in values)


def cases():
    values = [((i * 7919) % 2_001) - 1_000 for i in range(400_000)]
    return [("mixed-signs",  lambda: (list(values),)),
            ("all-negative", lambda: ([-abs(v) - 1 for v in values],))]
