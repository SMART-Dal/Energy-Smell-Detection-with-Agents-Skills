"""C12.S1 Inefficient Large-Stride Traversal -- walking a row-major array by column.

NumPy stores C-order by default, so a column walk touches one useful value per
cache line. This is the one taxonomy claim that is about the hardware rather
than the interpreter.
"""

import numpy as np


def before(a):
    total = 0.0
    for j in range(a.shape[1]):
        total += a[:, j].sum()
    return float(total)


def after(a):
    total = 0.0
    for i in range(a.shape[0]):
        total += a[i, :].sum()
    return float(total)


def cases():
    return [("large-square", lambda: (np.arange(2000 * 2000, dtype=np.float64).reshape(2000, 2000),)),
            ("small-square", lambda: (np.arange(16 * 16, dtype=np.float64).reshape(16, 16),))]
