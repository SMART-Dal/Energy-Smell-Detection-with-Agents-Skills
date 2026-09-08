"""C8.S2 Missing Derived-Value Reuse -- a `struct.Struct` built per call.

A second artefact with the same shape as the compiled pattern, and one where
the standard library does *not* cache for you -- so unlike the `re` case, what
is saved really is the derivation rather than a cache probe. Comparing the two
readings is how the card can say which of its examples is the honest one.
"""

import struct

_FORMAT = "<IHHf"
_STRUCT = struct.Struct(_FORMAT)


def before(records):
    return sum(struct.Struct(_FORMAT).pack(*r)[0] for r in records)


def after(records):
    return sum(_STRUCT.pack(*r)[0] for r in records)


def cases():
    records = [(i, i % 100, i % 7, float(i)) for i in range(200_000)]
    return [("large",  lambda: (list(records),)),
            ("normal", lambda: (records[:2_000],))]
