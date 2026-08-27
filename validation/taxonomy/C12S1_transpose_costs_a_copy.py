"""C12.S1 Inefficient Large-Stride Traversal -- the transpose
that fixes the stride costs a full copy.

"Transposing the iteration order or the array layout would improve cache hits"
is the description, and `C12S1_stride_traversal` measures the traversal swap at
+42.8%. Reordering the *loops* is free.

Reordering the *array* is not. The column sums genuinely have to be column sums,
so the iteration order cannot change; the only edit left is
`np.ascontiguousarray(matrix.T)`, which reads every element once with the bad
stride and writes it back with a good one. Over a single pass that is the misses
the traversal would have taken, paid up front, plus an allocation the size of
the matrix.

Two repairs wear this root cause's name and they are priced differently. Walking
the axis that is already contiguous is free; making a different axis contiguous
is an O(n) copy, and it only pays when the copied layout is then traversed many
times.
"""

import numpy as np


def before(matrix, passes):
    total = 0.0
    for _ in range(passes):
        for j in range(matrix.shape[1]):
            total += float(matrix[:, j].sum())
    return round(total, 3)


def after(matrix, passes):
    transposed = np.ascontiguousarray(matrix.T)     # one full copy, up front
    total = 0.0
    for _ in range(passes):
        for i in range(transposed.shape[0]):
            total += float(transposed[i, :].sum())
    return round(total, 3)


_MATRIX = np.arange(1_500 * 1_500, dtype=np.float64).reshape(1_500, 1_500)


def cases():
    return [("one-pass",   lambda: (_MATRIX, 1)),
            ("many-passes", lambda: (_MATRIX, 12)),
            ("edge",       lambda: (np.zeros((2, 2), dtype=np.float64), 1))]
