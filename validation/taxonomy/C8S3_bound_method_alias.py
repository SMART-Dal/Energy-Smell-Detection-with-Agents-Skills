"""C8.S3 Repeated Attribute Resolution -- a bound method resolved per iteration.

The classic Python form, and the only one whose cost is an object rather than a
dict probe: `out.append` and `self._transform` each allocate a fresh bound
method every time they are read. The measured files for this root cause all
hoist a plain attribute chain, which pays the probe and not the allocation.

The card is explicit that a comprehension is usually the better answer and
would subsume this under C3.S1. The alias form is for the cases where a
comprehension is not available, which is why it is measured as written.
"""


class Transformer:
    __slots__ = ("scale",)

    def __init__(self, scale):
        self.scale = scale

    def _transform(self, value):
        return value * self.scale + 1


def before(transformer, values):
    out = []
    for value in values:
        out.append(transformer._transform(value))
    return out


def after(transformer, values):
    out = []
    append = out.append
    transform = transformer._transform
    for value in values:
        append(transform(value))
    return out


def cases():
    return [("large",  lambda: (Transformer(3), list(range(400_000)))),
            ("normal", lambda: (Transformer(3), list(range(4_000))))]
