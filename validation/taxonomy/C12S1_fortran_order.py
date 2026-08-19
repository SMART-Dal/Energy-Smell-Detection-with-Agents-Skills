"""C12.S1 Column-Major Traversal -- the mirror image, on a Fortran-ordered
array.

The card says to read `arr.flags` rather than assume, because a transpose or an
`asfortranarray` upstream flips which axis is contiguous. Here the *column*
walk is the fast one and the row walk is the mistake, which is the same root
cause with the repair pointing the other way -- and a rule that pattern-matched
`arr[:, j]` would have it exactly backwards.
"""

import numpy as np


def before(matrix):
    total = 0.0
    for i in range(matrix.shape[0]):
        total += float(matrix[i, :].sum())
    return round(total, 3)


def after(matrix):
    total = 0.0
    for j in range(matrix.shape[1]):
        total += float(matrix[:, j].sum())
    return round(total, 3)


def _fortran(n, m):
    return np.asfortranarray(np.arange(n * m, dtype=np.float64).reshape(n, m))


def cases():
    return [("large",  lambda: (_fortran(4_000, 4_000),)),
            ("normal", lambda: (_fortran(400, 400),)),
            ("edge",   lambda: (_fortran(1, 1),))]
