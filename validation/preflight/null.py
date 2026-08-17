"""Identical code against itself: whatever this reads is the host's own noise."""

def _work(xs):
    total = 0
    for x in xs:
        total += (x * 3) ^ (x >> 2)
    return total


before = _work
after = _work


def cases():
    return [("null", lambda: (list(range(200_000)),))]
