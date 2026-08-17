"""C3.S6 Unfiltered Bulk Iteration -- materialising everything to take one item."""

def before(xs):
    return sorted(xs)[0]


def after(xs):
    return min(xs)


def cases():
    return [("large", lambda: ([(i * 7919) % 1_000_003 for i in range(300_000)],)),
            ("small", lambda: ([5, 3, 9, 1],))]
