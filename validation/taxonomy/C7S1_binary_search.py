"""C7.S1 Suboptimal Algorithm Choice -- a linear scan against a hand-written
binary search.

`bisect` is deliberately not used. It is a C implementation of the same
algorithm, so calling it would fold "O(log n) beats O(n)" together with "C beats
the interpreter" and the reading could not be attributed to either. Both halves
here are ordinary Python loops.

The sortedness is a precondition that already holds; if the function had to sort
first, the sort would dominate and the repair would be worthless for one lookup.
`small-n` is the crossover: over a handful of elements the scan wins on
constants, because a binary search still pays its arithmetic per step.
"""

def _scan(sorted_values, target):
    for position, value in enumerate(sorted_values):
        if value == target:
            return position
        if value > target:
            return -1
    return -1


def _bisect(sorted_values, target):
    low, high = 0, len(sorted_values)
    while low < high:
        middle = (low + high) // 2
        if sorted_values[middle] < target:
            low = middle + 1
        else:
            high = middle
    if low < len(sorted_values) and sorted_values[low] == target:
        return low
    return -1


def before(sorted_values, targets):
    found = 0
    for target in targets:
        position = _scan(sorted_values, target)
        if position >= 0:
            found += position
    return found


def after(sorted_values, targets):
    found = 0
    for target in targets:
        position = _bisect(sorted_values, target)
        if position >= 0:
            found += position
    return found


def cases():
    big = list(range(0, 200_000, 2))
    small = list(range(0, 16, 2))
    return [("large-n", lambda: (big, [(i * 7919) % 200_000 for i in range(2_000)])),
            ("small-n", lambda: (small, [(i * 7) % 16 for i in range(200_000)])),
            ("edge",    lambda: ([], [1]))]
