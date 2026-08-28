"""Cases for eager_comprehension."""


def total_doubled(values):
    # Materialised only for `sum` to walk it once.
    return sum([x * 2 for x in values])


def any_failed(results):
    # `any` stops early, so the list also computes elements it never reads.
    return any([r.failed for r in results])


def joined(rows):
    # `str.join` streams its argument too.
    return ", ".join([row.name for row in rows])


def unique_names(rows):
    # `set` builds a container of its own, so a generator saves no allocation.
    return set([row.name for row in rows])


def ranked(rows):
    # `sorted` likewise has to materialise everything anyway.
    return sorted([row.score for row in rows])


def spread(values):
    # Bound first, then consumed twice: a generator would be exhausted.
    doubled = [x * 2 for x in values]
    return max(doubled) - min(doubled)


def total_already_lazy(values):
    # Already a generator expression.
    return sum(x * 2 for x in values)


def sized(rows):
    # `len` needs a sequence.
    return len([row for row in rows if row.valid])


def weights_twice(rows):
    # Materialised because the result is reduced and then counted.
    weights = [row * 3 + 1 for row in rows]
    return sum(weights), len(weights)