"""C10.S4 -- string += where the accumulator is a plain, unaliased local.

This is the shape the published taxonomy uses as its example, and the shape the
old analyzer fired on. CPython resizes in place when the refcount is 1, so the
prediction is that the canonical repair does *nothing* here, or loses.

Javad's ImproperDataStructure/ConcatenateStrInLoop is exactly this shape and is
labelled a smell, so this case decides between the card and the sample.
"""

def before(parts):
    out = ""
    for p in parts:
        out += p
    return out


def after(parts):
    collected = []
    for p in parts:
        collected.append(p)
    return "".join(collected)


def cases():
    return [
        ("many-small", lambda: (["abcde"] * 200_000,)),
        ("few-large", lambda: (["abcde" * 1000] * 2_000,)),
    ]
