"""C1.S1 Dead Code -- a whole loop whose accumulator nothing reads.

A pass, N appends and a list of N objects, for a value the function already
had. The card's second repair example; here it is measured rather than argued.
"""

def before(records):
    checksums = []
    for record in records:
        checksums.append(record * 31 + 7)
    return len(records)


def after(records):
    return len(records)


def cases():
    return [("large",  lambda: (list(range(300_000)),)),
            ("normal", lambda: (list(range(3_000)),)),
            ("edge",   lambda: ([],))]
