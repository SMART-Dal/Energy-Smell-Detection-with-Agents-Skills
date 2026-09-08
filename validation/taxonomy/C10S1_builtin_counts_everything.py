"""C10.S1 Skipping Optimized Built-ins -- the built-in counts
everything and the caller wanted a hundredth of it.

This is Javad's OveruseOfLoops/OccurenceOfOddItems sample, which is where the
whole shape came from. The function reports how often each *odd* value appears.
`collections.Counter` is the obvious built-in for counting and its loop runs in
C, so the hand-written dict loop reads as the textbook instance of this root
cause -- and `C10S1_manual_sum` measures the same reasoning at +88.7% where it
holds.

The comprehension after the `Counter(...)` is what breaks it. The input is
overwhelmingly even, so `Counter` hashes and tallies six million values in order
to throw all but nine of them away, while the loop's `if x % 2 == 0: continue`
never lets them reach the dictionary at all. Six million C-level operations lose
to nine Python-level ones.

The question the card has to ask is not "is there a built-in for this" but "does
the built-in do the same amount of work". A filter *after* an aggregation is the
sign that the aggregation ran over the wrong set -- and the same trap is waiting
in `sum(...)` over a comprehension that discards most of its input, in
`sorted()` before a slice, and in `max()` over a mapped list.

`mostly-odd` is the same code on input the filter does not shrink, where the
built-in is ahead again.
"""

from collections import Counter


def before(values):
    counts = {}
    for value in values:
        if value % 2 == 0:
            continue                      # even values never reach the dict
        seen = counts.get(value, 0)
        counts[value] = seen + 1
    return counts


def after(values):
    counted = Counter(values)
    return {key: count for key, count in counted.items() if key % 2 == 1}


def _mostly_even(n):
    values = [i for i in range(0, 200, 2)] * (n // 100)
    values += [1, 3, 3, 5, 7, 1, 3, 9, 3]
    return values


def _mostly_odd(n):
    values = [i for i in range(1, 200, 2)] * (n // 100)
    values += [2, 4, 4, 6, 8, 2, 4, 10, 4]
    return values


def cases():
    return [("mostly-even", lambda: (_mostly_even(600_000),)),
            ("mostly-odd",  lambda: (_mostly_odd(600_000),))]
