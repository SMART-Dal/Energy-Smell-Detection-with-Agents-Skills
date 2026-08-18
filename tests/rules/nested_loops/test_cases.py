"""Cases for nested_loops."""


def pair_totals(rows, columns):
    # Two statement loops: the product of the counts.
    total = 0
    for row in rows:
        for column in columns:
            total += row.weight * column.weight
    return total


def cross_products(left, right):
    # The same nest written as comprehensions.
    return [[a * b for b in right] for a in left]


def drain_pending(queues):
    # A `while` inside a `for` nests just as much as two `for`s.
    seen = []
    for queue in queues:
        while queue:
            seen.append(queue.pop())
    return seen


def triple_scan(cube):
    # Three levels: reported once, at the innermost loop only.
    total = 0
    for plane in cube:
        for row in plane:
            for cell in row:
                total += cell
    return total


def two_inner_loops(rows):
    # Two separate innermost loops under one outer: two distinct nests.
    for row in rows:
        for cell in row.cells:
            cell.touch()
        for note in row.notes:
            note.touch()


def sum_then_scale(rows, factor):
    # Sequential loops at the same level are additive, not multiplicative.
    total = 0
    for row in rows:
        total += row.value
    scaled = []
    for row in rows:
        scaled.append(row.value * factor)
    return total, scaled


def outer_only(rows):
    # One loop calling something that may loop is still one loop here.
    return [summarise(row) for row in rows]


def make_counter(columns):
    # The nest belongs to the closure, not to the factory that returns it.
    def count(rows):
        total = 0
        for row in rows:
            for column in columns:
                total += row[column]
        return total

    return count
