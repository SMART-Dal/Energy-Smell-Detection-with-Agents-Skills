"""C7.S1 Suboptimal Algorithm Choice -- an insertion sort against Timsort.

The card is careful that this is C7.S1 rather than C10.S1: `sorted` is not the
same algorithm implemented in C, it is a different algorithm. Insertion sort is
quadratic on random data and linear on nearly-sorted data, which is exactly
where the card says to know the crossover -- so `nearly-sorted` is the case
where the hand-written version is competitive.
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


def before(values):
    return _insertion_sorted(values)


def after(values):
    return sorted(values)


def cases():
    scrambled = [(i * 7919) % 4_000 for i in range(4_000)]
    nearly = list(range(4_000))
    nearly[10], nearly[3_000] = nearly[3_000], nearly[10]
    return [("scrambled",     lambda: (list(scrambled),)),
            ("nearly-sorted", lambda: (list(nearly),)),
            ("edge",          lambda: ([],))]
