"""C3.S1 Inefficient Iteration Construct -- a comprehension
cannot stop.

An `append` loop with one statement in the body is the shape, and
`C3S1_index_iteration` measures the comprehension at +28.8%. The body here is
one `append` too -- the `break` is the second statement, and a comprehension has
nowhere to put it.

Written as a comprehension plus a slice, the loop runs to the end of the input
and the slice throws away what it did not need. Where the limit is a hundredth
of the collection, that is a hundred times the work in exchange for the faster
per-element construct.

The description's own wording is the test: an iteration form is only
interchangeable when the alternative *does the same iterations*. A `break`, a
`continue` with side effects, or an early `return` all remove that guarantee.
"""

def before(records, limit):
    out = []
    for record in records:
        out.append(record * 2 + 1)
        if len(out) >= limit:
            break
    return out


def after(records, limit):
    return [record * 2 + 1 for record in records][:limit]


def cases():
    return [("stops-early", lambda: (list(range(400_000)), 2_000)),
            ("takes-all",   lambda: (list(range(400_000)), 400_000)),
            ("edge",        lambda: ([], 10))]
