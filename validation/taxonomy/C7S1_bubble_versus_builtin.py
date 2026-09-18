"""C7.S1 Suboptimal Algorithm Choice -- a bubble sort against `sorted()`.

The taxonomy's own first example, which had no implementation: the measured
file for this root cause compares bubble against a *hand-written* merge sort,
which holds the language constant and isolates the complexity. That is the
right experiment for "is O(n log n) better than O(n^2)", and it is not the
comparison the taxonomy names.

This one names it. `sorted()` is Timsort in C, so the repair changes both the
complexity and the language the inner loop runs in, and the reading is the sum
of the two. That is what a reader following the card will actually write.
"""


def _bubble_sorted(values):
    a = list(values)
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a


def before(values):
    return _bubble_sorted(values)


def after(values):
    return sorted(values)


def cases():
    return [("scrambled", lambda: ([(i * 7919) % 10_007 for i in range(1_500)],)),
            ("nearly-sorted", lambda: (sorted((i * 7919) % 10_007
                                              for i in range(1_500)),))]
