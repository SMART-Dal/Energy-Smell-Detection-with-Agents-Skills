"""A saving no measurement rig should be able to miss.

5000-element linear scan against a hash lookup, a thousand times over. If this
does not read as a large saving, the meter is not watching this process.
"""

def before(haystack, needles):
    return sum(1 for n in needles if n in haystack)


def after(haystack, needles):
    lookup = set(haystack)
    return sum(1 for n in needles if n in lookup)


def cases():
    return [("linear-vs-hash", lambda: (list(range(5_000)), list(range(0, 5_000, 5))))]
