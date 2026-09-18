"""C3.S3 Inefficient Per-Iteration Setup -- a lambda rebuilt every iteration.

One of the three shapes the taxonomy names for this root cause, and the one
with no implementation. A `lambda` in a loop body is a `MAKE_FUNCTION` per
iteration: a fresh function object, with its own closure cell when it captures
anything, allocated and discarded each pass.

The other measured files hoist a compiled pattern and a file handle, where the
saving is a cache probe or a syscall. This one's saving is an allocation, which
is the smallest of the three and the one most likely to be written by accident.
"""


def before(batches):
    total = 0
    for batch in batches:
        key = lambda pair: pair[1]
        total += max(batch, key=key)[0]
    return total


def after(batches):
    key = lambda pair: pair[1]
    total = 0
    for batch in batches:
        total += max(batch, key=key)[0]
    return total


def _batches(count, width):
    return [[(i, (i * 7919 + j) % 1_000) for j in range(width)] for i in range(count)]


def cases():
    return [("many-small-batches", lambda: (_batches(200_000, 4),)),
            ("few-large-batches",  lambda: (_batches(2_000, 400),))]
