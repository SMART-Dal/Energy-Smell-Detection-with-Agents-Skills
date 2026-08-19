"""C10.S3 Missing Bulk Operations -- a Python loop over a numeric array.

The card says iterating a numeric array element by element is the worst of both
worlds -- unboxing per element on top of interpreter overhead -- so the saving
from vectorising is much larger there than the general figure. This is the
claim that most justifies the whole category, and the small case says whether
the array setup swamps it.
"""

import numpy as np


def before(values, factor):
    total = 0.0
    for i in range(values.shape[0]):
        total += float(values[i]) * factor
    return round(total, 3)


def after(values, factor):
    return round(float((values * factor).sum()), 3)


def cases():
    return [("large",  lambda: (np.arange(1_000_000, dtype=np.float64), 1.5)),
            ("normal", lambda: (np.arange(2_000, dtype=np.float64), 1.5)),
            ("edge",   lambda: (np.zeros(0, dtype=np.float64), 1.5))]
