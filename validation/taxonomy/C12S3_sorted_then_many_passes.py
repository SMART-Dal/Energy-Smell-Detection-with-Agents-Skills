"""C12.S3 Unpredictable Branches -- sorting to make the branch predictable,
amortised over many passes.

The card says sorting is n log n work to save n/2 mispredictions, so it pays
only when the sorted data is traversed many times. The other C12.S3 case makes
one pass and loses; this one varies the pass count, which is the variable the
card names. It also stays in interpreted Python deliberately, so the answer is
about the same interpreter the agent will be reading.
"""

def before(values, passes):
    total = 0
    for _ in range(passes):
        for x in values:
            if x > 0:
                total += x
    return total


def after(values, passes):
    ordered = sorted(values)
    total = 0
    for _ in range(passes):
        for x in ordered:
            if x > 0:
                total += x
    return total


def _unpredictable(n):
    return [(i * 7919) % 2001 - 1000 for i in range(n)]


def cases():
    return [("many-passes", lambda: (_unpredictable(200_000), 20)),
            ("one-pass",    lambda: (_unpredictable(200_000), 1)),
            ("edge",        lambda: ([], 1))]
