"""C3.S6 Unfiltered Bulk Processing -- deduplicate before the per-element test.

From the project's sample set, and the card carries it as the clearest example
of a reduction that only pays at a high duplicate ratio: a million values drawn
from a hundred distinct ones means one hashing pass replaces almost all of the
comparisons, and on unique data the same pass is pure overhead.

`dense-duplicates` and `all-unique` are the two ends. The predicate is
deliberately expensive so the skipped work is worth skipping.
"""

def _expensive(x):
    total = 0
    for i in range(1, 24):
        total += (x * i) % 7
    return total % 3 == 0


def before(values):
    return {x for x in values if _expensive(x)}


def after(values):
    return {x for x in set(values) if _expensive(x)}


def cases():
    return [("dense-duplicates", lambda: ([i % 101 for i in range(200_000)],)),
            ("all-unique",       lambda: (list(range(200_000)),)),
            ("edge",             lambda: ([],))]
