"""C12.S1 Column-Major Traversal -- the same stride on an array that fits in
cache.

The card's precondition, measured: this is a cache-miss effect, so below
last-level cache every line is resident and the stride costs almost nothing.
The other C12.S1 case uses an array far larger than cache and reads +42.8%; if
this one reads near zero, the card can say where the boundary is instead of
saying "large enough".
"""

import numpy as np


def before(matrix):
    total = 0.0
    for j in range(matrix.shape[1]):
        total += float(matrix[:, j].sum())
    return round(total, 3)


def after(matrix):
    total = 0.0
    for i in range(matrix.shape[0]):
        total += float(matrix[i, :].sum())
    return round(total, 3)


def cases():
    small = np.arange(256 * 256, dtype=np.float64).reshape(256, 256)   # 512 KB
    tiny = np.arange(32 * 32, dtype=np.float64).reshape(32, 32)        # 8 KB
    return [("fits-in-l2", lambda: (small.copy(),)),
            ("tiny",       lambda: (tiny.copy(),)),
            ("edge",       lambda: (np.zeros((1, 1), dtype=np.float64),))]
