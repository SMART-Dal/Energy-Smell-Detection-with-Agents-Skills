"""C5.S2 Missing Helper Type -- a set beside a list that is still the answer.

The card's second repair example, and what separates this root cause from a
change of container type: `kept` stays a list because the function returns it
and first-seen order matters. Two structures afterwards rather than one changed
one.

`all-distinct` is the adversarial case: with no duplicates the set is built and
never saves a scan it would not have finished anyway.
"""

def before(rows):
    kept = []
    for row in rows:
        if row not in kept:
            kept.append(row)
    return kept


def after(rows):
    kept = []
    seen = set()
    for row in rows:
        if row not in seen:
            seen.add(row)
            kept.append(row)
    return kept


def cases():
    return [("many-duplicates", lambda: ([i % 500 for i in range(40_000)],)),
            ("all-distinct",    lambda: (list(range(20_000)),))]
