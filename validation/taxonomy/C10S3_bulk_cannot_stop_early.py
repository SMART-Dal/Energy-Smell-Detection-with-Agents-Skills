"""C10.S3 Missing Bulk Primitive Usage -- the bulk call has to
consume the whole source.

"Calling list.append() in a loop when list.extend() would batch the operation"
is the description, and `C10S3_append_to_extend` measures it at +82%. `extend`
resolves one attribute, makes one call and copies pointers in C.

To do that it has to reach the end of the iterable. The loop here stops when it
has enough, so `append` runs a few thousand times against a source of half a
million; `extend` runs the generator to exhaustion and the slice afterwards
throws away everything past the limit. One C-level loop over 500_000 elements
loses to a Python-level loop over 2_000.

A bulk primitive is a promise to process everything. Where the consumer is
bounded -- a limit, a `break`, a timeout, a first match -- the per-element form
is doing strictly less work, and `itertools.islice` is the primitive that
applies.
"""

def _source(n):
    return ((i * 7919) % 1_000 for i in range(n))


def before(size, limit):
    out = []
    for value in _source(size):
        out.append(value)
        if len(out) >= limit:
            break
    return len(out), out[-1]


def after(size, limit):
    out = []
    out.extend(_source(size))
    out = out[:limit]
    return len(out), out[-1]


def cases():
    return [("stops-early", lambda: (500_000, 2_000)),
            ("takes-all",   lambda: (500_000, 500_000)),
            ("edge",        lambda: (10, 1))]
