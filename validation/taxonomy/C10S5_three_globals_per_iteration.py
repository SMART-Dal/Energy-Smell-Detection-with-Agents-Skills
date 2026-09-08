"""C10.S5 Global Variable Access In Loops -- three global reads per iteration.

The card says a single global read in a loop is advisory and suggests three or
more before calling it a finding. This is that shape: three module-level names
resolved per element against three locals bound once. The loop body does
nothing else, which is the most favourable case there is -- so this reading is
an upper bound on the root cause rather than a typical one.
"""

import math

SCALE = 3.5
OFFSET = 1.25


def before(values):
    total = 0.0
    for value in values:
        total += math.sqrt(value) * SCALE + OFFSET
    return round(total, 3)


def after(values):
    # Only the two module globals are bound. `math.sqrt` stays where it is in
    # both variants: hoisting it as well is an attribute lookup on an imported
    # module, which is C8.S3, and folding the two together made the reading
    # unattributable to either.
    scale, offset = SCALE, OFFSET
    total = 0.0
    for value in values:
        total += math.sqrt(value) * scale + offset
    return round(total, 3)


def cases():
    return [("large",  lambda: (list(range(2_000_000)),)),
            ("normal", lambda: (list(range(20_000)),))]
