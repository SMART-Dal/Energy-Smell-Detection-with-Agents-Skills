"""C7.S1 Suboptimal Algorithm Choice -- bubble sort against merge sort.

Both variants are hand-written Python. That is the point: this root cause is
about the *algorithm*, and comparing a Python loop against `sorted()` would
measure CPython's C implementation instead. Timsort would win here whatever
algorithm it replaced, which tells the reader nothing about complexity.

Same language, same interpreter, same data; only the exponent differs.
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


def _merge_sorted(values):
    a = list(values)
    if len(a) < 2:
        return a
    middle = len(a) // 2
    left = _merge_sorted(a[:middle])
    right = _merge_sorted(a[middle:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def before(values):
    return _bubble_sorted(values)


def after(values):
    return _merge_sorted(values)


def cases():
    return [("large",  lambda: ([(i * 7919) % 10_007 for i in range(1_500)],))]
