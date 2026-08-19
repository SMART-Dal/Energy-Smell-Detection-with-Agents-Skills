"""C1.S7 Unnecessary Variable -- the temporary that is a symptom of a bigger
repair.

The card says a single-use temporary inside a loop is usually a symptom: an
`append` loop that wants to be a comprehension. So this pair does *both* edits,
which makes it a deliberate test of the card's own advice to report the larger
finding (C3.S1 or C10.S3) and subsume this one. If the reading here is much
larger than the plain inlining case, the advice is right.
"""

def before(records):
    out = []
    for record in records:
        digest = record * 31 + 7
        out.append(digest)
    return out


def after(records):
    return [record * 31 + 7 for record in records]


def cases():
    return [("large",  lambda: (list(range(1_000_000)),)),
            ("normal", lambda: (list(range(10_000)),)),
            ("edge",   lambda: ([],))]
