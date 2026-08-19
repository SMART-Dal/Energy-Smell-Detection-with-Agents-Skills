"""C3.S7 Collection Modification During Iteration -- already correct, and the
remaining cost is somebody else's.

The card's first `NOT a smell when` clause: `for item in list(pending)` walks a
snapshot, so the mutation cannot disturb the iterator and the code is right as
written. What is left is that `remove` is a linear scan per item, which makes
it quadratic -- and the card says that finding is C7.S1, not this one.

So `after` here applies the C7.S1 repair, and a large reading says the card is
right to send the reader elsewhere rather than that C3.S7 applies.
"""

def before(pending):
    snapshot = list(pending)
    for item in snapshot:
        if item % 2 == 0:
            pending.remove(item)
    return pending


def after(pending):
    pending[:] = [item for item in pending if item % 2]
    return pending


def cases():
    return [("large",  lambda: (list(range(30_000)),)),
            ("normal", lambda: (list(range(300)),)),
            ("edge",   lambda: ([],))]
