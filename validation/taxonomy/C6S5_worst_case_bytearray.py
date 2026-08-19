"""C6.S5 Over-Allocation -- a buffer sized for the worst case, per call.

The card says the zeroing of a large buffer is real CPU work and shows up when
the allocation happens per call rather than once, and that the gap has to be an
order of magnitude rather than a factor of two. `close-fit` is the factor-of-
two case, which should read as nothing.
"""

def before(payload, reserve):
    buffer = bytearray(reserve)
    for i, byte in enumerate(payload):
        buffer[i] = byte
    return bytes(buffer[:len(payload)])


def after(payload, reserve):
    buffer = bytearray(len(payload))
    for i, byte in enumerate(payload):
        buffer[i] = byte
    return bytes(buffer)


def cases():
    small = bytes(range(256)) * 4        # 1 KB
    return [("hugely-oversized", lambda: (small, 1_000_000)),
            ("close-fit",        lambda: (small, 2_048)),
            ("edge",             lambda: (b"", 1_000_000))]
