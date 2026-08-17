"""C7.S1 Suboptimal Algorithm Choice -- bubble sort against Timsort.

The largest effect in the suite by design. If this does not confirm, nothing
else in the results should be believed.
"""

def before(xs):
    a = list(xs)
    n = len(a)
    for i in range(n):
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


def after(xs):
    return sorted(xs)


def cases():
    return [("large", lambda: ([(i * 7919) % 10_007 for i in range(1_200)],)),
            ("small", lambda: ([3, 1, 2],)),
            ("empty", lambda: ([],))]
