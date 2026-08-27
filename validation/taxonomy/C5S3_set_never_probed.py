"""C5.S3 Over-Provisioned Data Type -- a set used only to collect.

From Javad's BuiltInBehavior/GreaterThanK1 and UniqueDivisbleByK1, where the
accumulator is a `set` and every element added to it is already distinct.

A set costs a hash and a probe on every `add` in exchange for deduplication and
O(1) membership. This loop never asks about membership, and the values are
distinct by construction -- they are derived from an index -- so the
deduplication has nothing to remove. `list.append` writes a pointer.

Both variants return the same sorted list, so the deduplication genuinely is
dead weight rather than a difference the caller could see. The card's test is
which operations the container's cost is buying, and an accumulator that is
never probed and never collides is buying neither of a set's two properties.
"""

def before(values, floor):
    kept = set()
    for value in values:
        if value > floor:
            kept.add(value)
    return sorted(kept)


def after(values, floor):
    kept = []
    for value in values:
        if value > floor:
            kept.append(value)
    return sorted(kept)


def cases():
    return [("all-distinct", lambda: (list(range(400_000)), -1)),
            ("mostly-cut",   lambda: (list(range(400_000)), 399_000)),
            ("edge",         lambda: ([], 0))]
