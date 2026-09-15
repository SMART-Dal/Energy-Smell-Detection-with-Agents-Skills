"""Cases for column_major_traversal."""

import numpy as np


def column_sums(matrix):
    # Walks a column of a C-ordered array: one useful value per cache line.
    totals = []
    for j in range(matrix.shape[1]):
        totals.append(matrix[:, j].sum())
    return totals


def column_maxima(matrix):
    # The same access written as a comprehension.
    return [matrix[:, j].max() for j in range(matrix.shape[1])]


def row_sums(matrix):
    # Along the contiguous axis: the repaired direction.
    return [matrix[i, :].sum() for i in range(matrix.shape[0])]


def whole_array(matrix):
    # No per-column loop at all.
    return np.asarray(matrix).sum(axis=0)


def one_column(matrix, index):
    # Outside any loop.
    return matrix[:, index].mean()


def scalar_cells(matrix):
    # Both indices are scalars, so there is no stride to get wrong.
    total = 0
    for i in range(matrix.shape[0]):
        total += matrix[i, 0]
    return total


def pandas_column_means(frame, width):
    # Quiet. The shape matches exactly -- `[slice, non-slice]` -- but the
    # reasoning does not survive a pandas accessor: `.iloc`'s own overhead
    # dwarfs the memory layout. Over a 400x400 frame, column-wise measured
    # 21.61 ms against 21.19 ms row-wise, a 2% spread that is noise, while the
    # same traversal on the underlying ndarray ran 0.81 and 0.68 ms. There is
    # no saving to promise in either direction.
    total = 0
    for j in range(width):
        total += frame.iloc[:, j].mean()
    return total


def through_values(frame, width):
    # Fires: `.values` hands back a real ndarray, so the cache argument applies
    # again and the accessor overhead is gone.
    total = 0
    for j in range(width):
        total += frame.values[:, j].sum()
    return total
