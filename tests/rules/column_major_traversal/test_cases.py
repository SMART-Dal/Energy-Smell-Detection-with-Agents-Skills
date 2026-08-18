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
