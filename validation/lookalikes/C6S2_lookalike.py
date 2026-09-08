"""C6.S2 Unnecessary Copying -- LOOKS THE SAME, IS NOT: the copy was buying the
caller's ordering.

"Using sorted(lst) (which creates a new list) when lst.sort() (in-place) would
work" is the description's own example, and `C6S2_sorted_versus_sort` measures
it at +42.3% -- with `EQUIVALENCE = "returns_only"` declared, because the whole
difference is the side effect.

Here the side effect is observed. The caller sorts a copy to answer one
question, then uses the original in its own order to answer another. Sorting in
place answers the first question and destroys the input for the second, and both
answers are returned from the same function, so nothing crashes.

The description's test is "when a reference, view, slice, or in-place operation
would preserve correctness". A defensive copy is unnecessary when nothing reads
the original afterwards, and that is a question about the lines below the copy.
"""

def before(batches):
    total = 0
    for batch in batches:
        ordered = sorted(batch)
        total += ordered[0] + ordered[-1]
        total += batch[0]                # the caller's order still matters
    return total


def after(batches):
    total = 0
    for batch in batches:
        batch.sort()
        total += batch[0] + batch[-1]
        total += batch[0]
    return total


def _batches(count, width):
    return [[(i * 7919 + j * 31) % 1_000 for j in range(width)] for i in range(count)]


def cases():
    return [("many-batches", lambda: (_batches(40_000, 12),)),
            ("wide-batches", lambda: (_batches(400, 1_200),))]
