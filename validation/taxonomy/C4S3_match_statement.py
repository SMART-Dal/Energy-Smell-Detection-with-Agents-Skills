"""C4.S3 Inefficient Conditional Nesting -- the same chain written as
`match`/`case`.

The description names three repairs for a monolithic conditional: guard
clauses, dictionary dispatch, and `match`/`case`. The other two are measured --
`C4S3_dispatch_table` at +53.6% and `C4S3_guard_clauses` at -0.1% -- and this is
the third.

The comparison is deliberately narrow. Same tests, same order, same arms, same
bodies; only the construct differs. `match` on literal patterns is not a jump
table in CPython, it is a sequence of comparisons like the `elif` chain it
replaces, so the expectation is a reading near zero -- and if that is what comes
back, the card can say that this repair is a readability change and that only
the dispatch-table form carries an energy claim.

`late-match` sits on the last arm, where any difference in how the arms are
walked has the most room to show.
"""

def before(codes):
    total = 0
    for code in codes:
        if code == "created":
            total += 1
        elif code == "queued":
            total += 2
        elif code == "running":
            total += 3
        elif code == "retried":
            total += 4
        elif code == "failed":
            total += 5
        else:
            total += 6
    return total


def after(codes):
    total = 0
    for code in codes:
        match code:
            case "created":
                total += 1
            case "queued":
                total += 2
            case "running":
                total += 3
            case "retried":
                total += 4
            case "failed":
                total += 5
            case _:
                total += 6
    return total


def cases():
    return [("late-match",  lambda: (["failed"] * 400_000,)),
            ("early-match", lambda: (["created"] * 400_000,)),
            ("edge",        lambda: ([],))]
