"""C6.S2 Unnecessary Copying -- a defensive copy nothing mutates.

Also the measured test of the `copy_in_loop` analyzer added this pass.
"""

def before(rows):
    total = 0
    for r in rows:
        snapshot = list(r)
        total += snapshot[0]
    return total


def after(rows):
    total = 0
    for r in rows:
        total += r[0]
    return total


def cases():
    return [("large", lambda: ([list(range(32))] * 100_000,)),
            ("small", lambda: ([list(range(32))] * 20,)),
            ("empty", lambda: ([],))]
