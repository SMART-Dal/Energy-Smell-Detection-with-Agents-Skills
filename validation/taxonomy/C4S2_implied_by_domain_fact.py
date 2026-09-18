"""C4.S2 Determined Condition -- a test whose answer arithmetic already fixed.

`math.floor(v) <= math.ceil(v)` for every real number, so `ceiling < limit`
implies `floor < limit` and the second operand of the `and` can never decide
anything. The card uses this to say why no static rule finds this root cause:
the two tests are textually different and only a fact about the arithmetic
makes one redundant. The only other measured redundancy in this root cause is
textually identical, which is the case a rule *can* find.
"""

import math


def _classify_before(value, limit):
    floor = math.floor(value)
    ceiling = math.ceil(value)
    if ceiling < limit and floor < limit:
        return 2
    if floor < limit:
        return 1
    return 0


def _classify_after(value, limit):
    floor = math.floor(value)
    ceiling = math.ceil(value)
    if ceiling < limit:
        return 2
    if floor < limit:
        return 1
    return 0


def before(values, limit):
    return sum(_classify_before(v, limit) for v in values)


def after(values, limit):
    return sum(_classify_after(v, limit) for v in values)


def cases():
    values = [((i * 7919) % 20_000) / 100.0 for i in range(300_000)]
    return [("mostly-below", lambda: (list(values), 500.0)),
            ("mostly-above", lambda: (list(values), -1.0))]
