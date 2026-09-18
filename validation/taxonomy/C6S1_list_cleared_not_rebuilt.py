"""C6.S1 Unnecessary Object -- one list cleared rather than a new one per pass.

The taxonomy's own example for this root cause, which had no implementation:
"creating a new empty list inside every loop iteration to collect temporary
results, when a single list created before the loop and cleared with .clear()
each iteration would avoid repeated allocation".

The other measured file reuses a user-defined instance. This one reuses a
builtin container, where the allocation is smaller and the `.clear()` is not
free -- so it is the weaker version of the claim and worth having its own
number rather than borrowing the object one's.

The precondition is the same and is what makes reuse legal: the scratch list
never escapes the iteration that filled it.
"""


def before(rows):
    total = 0
    for row in rows:
        scratch = []
        for i in range(row % 8):
            scratch.append(row + i)
        total += len(scratch)
    return total


def after(rows):
    total = 0
    scratch = []
    for row in rows:
        scratch.clear()
        for i in range(row % 8):
            scratch.append(row + i)
        total += len(scratch)
    return total


def cases():
    return [("many-rows", lambda: (list(range(400_000)),)),
            ("few-rows",  lambda: (list(range(4_000)),))]
