"""Cases for index_based_iteration."""


def doubled(values):
    # The index exists only to read `values[i]`.
    out = []
    for i in range(len(values)):
        out.append(values[i] * 2)
    return out


def absolute_gaps(first, second):
    # Two sequences on one index: `zip` is the repair, but it is still this.
    total = 0
    for i in range(len(first)):
        total += abs(first[i] - second[i])
    return total


def running_totals(values):
    # The index is used to read and to write; still an index-driven loop.
    out = [0] * len(values)
    for i in range(len(values)):
        out[i] = values[i] + (out[i - 1] if i else 0)
    return out


def positions_only(values):
    # No subscript at all: the index is the value being used.
    total = 0
    for i in range(len(values)):
        total += i
    return total


def sliding_pairs(values):
    # The subscript is `values[i + 1]`, which direct iteration cannot express.
    return [values[i] + values[i + 1] for i in range(len(values) - 1)]


def with_enumerate(values):
    # Already the repaired form.
    out = []
    for index, value in enumerate(values):
        out.append((index, value * 2))
    return out


def every_other(values):
    # A stride: `range(0, len(values), 2)` is not `range(len(values))`.
    out = []
    for i in range(0, len(values), 2):
        out.append(values[i])
    return out


def matrix_diagonal(grid):
    # An index-driven loop over one sequence used to read another.
    return [grid[i][i] for i in range(len(grid))]
