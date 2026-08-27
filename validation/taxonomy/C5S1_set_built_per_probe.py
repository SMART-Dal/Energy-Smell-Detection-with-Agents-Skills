"""C5.S1 Inefficient Data Structure Choice -- the set has to be
rebuilt for every lookup it serves.

`x in list` is O(n) and `x in set` is O(1); `C5S1_membership_list` measures the
repair at +99.2%. The asymptotics are not in doubt.

The container here is per-row data, six elements long, and it is consulted once.
Converting it costs six hashes and an allocation to replace at most six
comparisons -- and the six comparisons stop at the first hit. The complexity
argument holds for the number of lookups per container, and here that number is
one.

Read the ratio before the container: a set pays off over a list when it is built
once and probed many times. Built once and probed once, it is strictly more
work, whatever the length.
"""

def before(rows):
    kept = 0
    for value, allowed in rows:
        if value in allowed:
            kept += 1
    return kept


def after(rows):
    kept = 0
    for value, allowed in rows:
        if value in set(allowed):
            kept += 1
    return kept


def _rows(n, width):
    return [(i % (width + 2), tuple(range(width))) for i in range(n)]


def cases():
    return [("one-probe-each", lambda: (_rows(300_000, 6),)),
            ("wide-lists",     lambda: (_rows(20_000, 400),)),
            ("edge",           lambda: ([],))]
