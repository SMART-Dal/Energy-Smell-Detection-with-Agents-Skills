"""C6.S5 Over-Allocation -- and the direction the card warns about.

"Check that shrinking it does not simply move the cost": a container that grows
dynamically reallocates and copies, and doing that repeatedly can cost more
than the over-allocation did. Here `before` pre-sizes and `after` grows, so a
*negative* reading is the card being right about the trade rather than about
the root cause.
"""

def before(n):
    buffer = [0] * n
    for i in range(n):
        buffer[i] = i * 2
    return len(buffer)


def after(n):
    buffer = []
    for i in range(n):
        buffer.append(i * 2)
    return len(buffer)


def cases():
    return [("large",  lambda: (1_000_000,)),
            ("normal", lambda: (10_000,)),
            ("edge",   lambda: (0,))]
