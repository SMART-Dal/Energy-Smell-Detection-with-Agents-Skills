"""C7.S5 Unsimplified Operation -- LOOKS THE SAME, IS NOT: the algebra does not hold
for the values this code sees.

"Computing expressions with known-zero or known-identity terms" is the
description, and `C7S5_unsimplified` measures a real simplification at +90.9%.
`x * 0 + y * 1` really is `y` -- over the integers.

Over IEEE floats it is not. `inf * 0` is `nan`, `nan * 0` is `nan`, and
`-0.0 * 1` is `-0.0`, so the simplified expression differs on exactly the inputs
that a sensor feed, a division result or a parsed JSON document actually
produces. The unsimplified version propagates the `nan`, which is what the
caller's downstream check is looking for; the simplified one hands back a clean
number and the bad reading is never noticed.

Algebraic identities the interpreter cannot apply are usually identities the
*type* does not have. Integers, yes; floats, decimals with a context, numpy
arrays with masks, and anything with `__mul__` of its own, no.
"""

import math


def before(readings, damping):
    out = []
    for value in readings:
        out.append(value * damping + value * 1.0)
    return sum(0.0 if math.isnan(v) else v for v in out), sum(
        1 for v in out if math.isnan(v))


def after(readings, damping):
    out = []
    for value in readings:
        out.append(value)                    # damping is 0.0, so "x*0 + x*1 == x"
    return sum(0.0 if math.isnan(v) else v for v in out), sum(
        1 for v in out if math.isnan(v))


def _readings(n, with_infinities):
    out = []
    for i in range(n):
        if with_infinities and i % 5_000 == 0:
            out.append(math.inf)
        else:
            out.append((i % 997) / 7.0)
    return out


def cases():
    return [("has-infinities", lambda: (_readings(300_000, True), 0.0)),
            ("finite-only",    lambda: (_readings(300_000, False), 0.0)),
            ("edge",           lambda: ([], 0.0))]
