"""Cases for sort_then_slice."""


def top_k(values, k):
    # Sorts everything to keep k.
    return sorted(values, reverse=True)[:k]


def cheapest(offers):
    # `sorted(...)[0]` is `min` with extra steps.
    return sorted(offers, key=lambda o: o.price)[0]


def newest(events):
    # `[-1]` is `max`.
    return sorted(events, key=lambda e: e.at)[-1]


def sum_top(values, k):
    # The slice can be nested inside another call.
    return sum(sorted(values)[:k])


def full_ranking(values):
    # Every element is kept, so the sort is the answer.
    return sorted(values)


def middle_value(values):
    # A single index that is neither end needs the whole ordering.
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def slice_unsorted(values, k):
    # No sort involved.
    return values[:k]


def sorted_then_bound(values, k):
    # Bound first: the rule only sees the inline form, which is honest about
    # what it can prove -- the name could be indexed anywhere.
    ordered = sorted(values)
    return ordered[:k]
