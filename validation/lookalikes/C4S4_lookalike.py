"""C4.S4 Missing Else-If -- LOOKS THE SAME, IS NOT: the conditions overlap.

Several bare `if`s testing the same variable, arms that look like a partition,
and an `elif` chain that stops at the first match: `C4S4_missing_elif` measures
that at +22.6% and `C4S4_many_arms_late_match` at +82.1%.

These arms are not exclusive. A row can be both stale and oversized, and the
independent `if`s apply both surcharges; an `elif` chain applies the first and
silently drops the rest. The output is smaller and nothing raises.

The description's own wording is "when the branches are mutually exclusive", and
that is a fact about the predicates rather than about the shape. Testing the
same variable is not the same as partitioning it -- ranges that touch,
`in`-tests over overlapping sets, and independent boolean flags all read like a
partition and are not one.
"""

def before(rows):
    total = 0
    for age, size in rows:
        surcharge = 0
        if age > 30:
            surcharge += 5
        if size > 100:
            surcharge += 7
        if size > 1_000:
            surcharge += 11
        total += surcharge
    return total


def after(rows):
    total = 0
    for age, size in rows:
        surcharge = 0
        if age > 30:
            surcharge += 5
        elif size > 100:
            surcharge += 7
        elif size > 1_000:
            surcharge += 11
        total += surcharge
    return total


def cases():
    return [("overlapping", lambda: ([(i % 60, (i * 7919) % 4_000) for i in range(400_000)],)),
            ("disjoint",    lambda: ([(i % 20, i % 90) for i in range(400_000)],)),
            ("edge",        lambda: ([],))]
