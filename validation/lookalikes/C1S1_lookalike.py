"""C1.S1 Dead Code -- LOOKS THE SAME, IS NOT: the discarded value came from a call that
also moved something.

Reads exactly like the root cause. A name is bound, nothing ever reads it, and
deleting the line is the obvious repair -- the taxonomy's own example is
"assignments to local variables that are never subsequently read".

The trick is on the right-hand side. `record.pop(0)` returns the header and
*removes* it, so the binding is dead and the call is not. Deleting the statement
leaves the header in the record and every subsequent `sum` is wrong.

What separates this from a real dead store is one question: does the expression
being discarded do anything besides produce a value? `sorted(x)` does not.
`x.pop()`, `x.sort()`, `next(it)`, `d.setdefault(k, v)` and `q.get()` all do.
"""

def before(records):
    kept = 0
    for record in records:
        header = record.pop(0)          # bound, never read -- but it also pops
        kept += sum(record)
    return kept


def after(records):
    kept = 0
    for record in records:
        kept += sum(record)
    return kept


def _records(n, width):
    return [[1000] + list(range(width)) for _ in range(n)]


def cases():
    return [("many-records", lambda: (_records(40_000, 8),)),
            ("wide-records", lambda: (_records(400, 800),))]
