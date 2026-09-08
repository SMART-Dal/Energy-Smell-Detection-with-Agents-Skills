"""C6.S1 Unnecessary Object -- LOOKS THE SAME, IS NOT: the reused buffer is the object
the caller kept.

This is the taxonomy's own repair, quoted: "a single list created before the
loop and cleared with .clear() each iteration would avoid repeated allocation".
One allocation instead of N is real, and where the per-iteration list is
genuinely temporary it is the right change.

The list is not temporary here -- it is appended to `groups`, so the caller
holds a reference to every one of them. Reusing one buffer means all N entries
in `groups` are the same object, and `.clear()` empties every one of them at
once. The result is a list of N empty lists.

The precondition is that nothing outlives the iteration. Reuse is safe for a
scratch buffer read and discarded inside the body; it is wrong the moment the
object is stored, returned, yielded or closed over.
"""

def before(rows):
    groups = []
    for row in rows:
        batch = []
        for i in range(row % 5):
            batch.append(row + i)
        groups.append(batch)
    return sum(len(g) for g in groups)


def after(rows):
    groups = []
    batch = []
    for row in rows:
        batch.clear()
        for i in range(row % 5):
            batch.append(row + i)
        groups.append(batch)
    return sum(len(g) for g in groups)


def cases():
    return [("many-rows", lambda: (list(range(300_000)),)),
            ("few-rows",  lambda: (list(range(300)),))]
