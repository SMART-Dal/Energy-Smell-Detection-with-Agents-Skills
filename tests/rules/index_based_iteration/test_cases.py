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
    # An indexed *write*, and a neighbour read beside it. `for value in values`
    # gives neither: rebinding the loop variable does not touch `out`, and
    # `out[i - 1]` needs the offset. A prefix sum is not this repair.
    out = [0] * len(values)
    for i in range(len(values)):
        out[i] = values[i] + (out[i - 1] if i else 0)
    return out


def strip_in_place(items):
    # A write-back. Direct iteration cannot express it -- `for item in items:
    # item = item.strip()` rebinds a local and leaves the list untouched -- but
    # `enumerate` can, and the read half `items[i]` still goes away. Declining
    # outright treated "no direct-iteration repair" as "no repair".
    for i in range(len(items)):
        items[i] = items[i].strip()


def find_position(items, target):
    # The index is the answer, so it cannot be dropped -- `enumerate` is the
    # repair, not direct iteration. This was silent until the rule learned to
    # say so: carrying the index out of the loop used to abandon the finding
    # rather than change the advice, which left the shape C3.S1 names first as
    # the one shape it never reported.
    for i in range(len(items)):
        if items[i] == target:
            return i
    return -1


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
    # A stride: not `range(len(values))`, but the index is doing the same job
    # and `values[::2]` walks the same elements without one. What changes is
    # the repair, which is worth saying rather than a reason to stay quiet.
    out = []
    for i in range(0, len(values), 2):
        out.append(values[i])
    return out


def matrix_diagonal(grid):
    # An index-driven loop over one sequence used to read another.
    return [grid[i][i] for i in range(len(grid))]


def reverse_walk(values):
    # A reverse walk is still an index doing the sequence's job; `reversed`
    # does it without one. Declining because it is not literally
    # `range(len(xs))` treated a different repair as no repair.
    for i in range(len(values) - 1, -1, -1):
        use(values[i])
