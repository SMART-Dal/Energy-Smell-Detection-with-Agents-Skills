"""C6.S5 Over-Allocation -- reserving far more than the input needs."""

def before(xs):
    buffer = [0] * 1_000_000
    for i, x in enumerate(xs):
        buffer[i] = x
    return buffer[:len(xs)]


def after(xs):
    buffer = [0] * len(xs)
    for i, x in enumerate(xs):
        buffer[i] = x
    return buffer


def cases():
    return [("tiny-input", lambda: (list(range(100)),)),
            ("full-input", lambda: (list(range(1_000_000)),))]
