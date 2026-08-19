"""C7.S1 Suboptimal Algorithm Choice -- a linear scan over sorted data.

The card's first repair example, and it insists on naming both algorithms and
saying roughly where they cross. `small-n` is that crossover: with a handful of
elements the scan wins on constants, which the card's first `NOT a smell when`
clause claims and nothing has measured.

The sortedness is a precondition that already holds here; if the function had
to sort first, the sort would dominate and the repair would be worthless for a
single lookup.
"""

import bisect


def before(sorted_values, targets):
    found = 0
    for target in targets:
        for position, value in enumerate(sorted_values):
            if value == target:
                found += position
                break
            if value > target:
                break
    return found


def after(sorted_values, targets):
    found = 0
    for target in targets:
        position = bisect.bisect_left(sorted_values, target)
        if position < len(sorted_values) and sorted_values[position] == target:
            found += position
    return found


def cases():
    big = list(range(0, 200_000, 2))
    small = list(range(0, 16, 2))
    return [("large-n", lambda: (big, [(i * 7919) % 200_000 for i in range(2_000)])),
            ("small-n", lambda: (small, [(i * 7) % 16 for i in range(200_000)])),
            ("edge",    lambda: ([], [1]))]
