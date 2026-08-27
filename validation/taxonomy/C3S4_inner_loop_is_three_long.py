"""C3.S4 Inefficient Nested Iteration -- the inner loop is
three elements long.

Two nested loops with a membership test in the inner one is the shape, and
`C3S4_nested_scan` measures the set repair at +99.5%. The complexity argument is
sound: O(n*m) becomes O(n+m).

It is sound about the exponents and silent about the constants. `m` here is
three, so the scan the set replaces is at most three comparisons, and the set
has to be built once per outer element because `allowed` is per-row data. That
is an allocation, three hashes and a hash per lookup, to avoid three
comparisons.

The description says the repair applies "over large data where the inner loop
performs linear search". Both words matter, and the inner size is the one that
gets assumed rather than read.
"""

def before(rows):
    kept = 0
    for row, allowed in rows:
        for permitted in allowed:
            if row == permitted:
                kept += 1
                break
    return kept


def after(rows):
    kept = 0
    for row, allowed in rows:
        if row in set(allowed):
            kept += 1
    return kept


def _rows(n, width):
    return [(i % (width + 2), tuple(range(width))) for i in range(n)]


def cases():
    return [("tiny-inner",  lambda: (_rows(300_000, 3),)),
            ("large-inner", lambda: (_rows(3_000, 400),)),
            ("edge",        lambda: ([],))]
