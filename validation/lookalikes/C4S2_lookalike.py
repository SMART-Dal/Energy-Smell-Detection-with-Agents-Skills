"""C4.S2 Redundant Conditional Evaluation -- LOOKS THE SAME, IS NOT: the branch between
the two tests is what changes the answer.

Two identical comparisons on the same variable in the same branch path is the
shape the description names -- "testing a variable twice in the same branch path
without any intervening modification" -- and `C4S2_redundant_condition` measures
deleting the second at +16.4%.

The intervening modification here is the `if` body. `depth` is decremented
inside the first branch, so by the time the second test runs it is a different
number, and the loop that reads as belt-and-braces is a two-step ladder.

The clause "without any intervening modification" is the whole test, and it is
about the statements between the two evaluations rather than about the two
expressions matching.
"""

def before(items, ceiling):
    kept = 0
    for item in items:
        depth = item % 5
        if depth > 0:
            depth -= 1                    # the intervening modification
            if depth > 0:
                kept += ceiling
    return kept


def after(items, ceiling):
    kept = 0
    for item in items:
        depth = item % 5
        if depth > 0:
            depth -= 1
            kept += ceiling               # "already established"
    return kept


def cases():
    return [("mixed-depths", lambda: (list(range(400_000)), 3)),
            ("all-deep",     lambda: ([i * 5 + 4 for i in range(400_000)], 3)),
            ("edge",         lambda: ([], 3))]
