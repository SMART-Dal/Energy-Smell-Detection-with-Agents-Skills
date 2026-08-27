"""C7.S1 Suboptimal Algorithm Choice -- the better complexity
loses at the size this code actually sees.

`C7S1_algorithm_choice` compares the same two algorithms at n = 1500 and merge
sort wins outright. Nothing about the code changes here; only n does.

Insertion sort is O(n^2) and merge sort is O(n log n), and for n = 12 the
quadratic one is faster: it allocates nothing, touches one list, and its inner
`while` usually exits immediately, where merge sort slices, recurses four levels
deep and builds a new list at every level. The batches here are twelve elements
because that is what the caller produces, and there are a lot of them.

Complexity is a statement about the limit. The finding needs the size the input
actually takes, and where that size is small and fixed, the constant factors are
the whole comparison.
"""

def _insertion_sorted(values):
    out = list(values)
    for i in range(1, len(out)):
        key = out[i]
        j = i - 1
        while j >= 0 and out[j] > key:
            out[j + 1] = out[j]
            j -= 1
        out[j + 1] = key
    return out


def _merge_sorted(values):
    a = list(values)
    if len(a) < 2:
        return a
    middle = len(a) // 2
    left, right = _merge_sorted(a[:middle]), _merge_sorted(a[middle:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:]); out.extend(right[j:])
    return out


def before(batches):
    return sum(_insertion_sorted(b)[0] for b in batches)


def after(batches):
    return sum(_merge_sorted(b)[0] for b in batches)


def _batches(count, width):
    return [[(i * 7919 + j * 31) % 1_000 for j in range(width)] for i in range(count)]


def cases():
    return [("small-batches", lambda: (_batches(20_000, 12),)),
            ("large-batches", lambda: (_batches(200, 1_200),)),
            ("edge",          lambda: ([[1]],))]
