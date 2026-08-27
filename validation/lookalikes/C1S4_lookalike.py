"""C1.S4 Repeated Computation -- LOOKS THE SAME, IS NOT: the second call is not the
same call.

The pattern matches on sight: `len(pending)` on two lines a few statements
apart, with the same argument, so bind it once and use it twice. The taxonomy's
own example is "calling len(data) in two consecutive lines when the list has not
been modified between the calls" -- and the clause that does the work is the
last one.

Between the two reads here, `pending.append(...)` runs. Hoisting the first read
freezes a length that the loop then changes, and every `budget` after the first
iteration is computed from a stale number.

The repair is available only when nothing between the two evaluations can affect
either the receiver or the arguments. That is a question about the statements in
between, not about the two expressions being textually equal.
"""

def before(jobs, ceiling):
    pending = []
    accepted = 0
    for job in jobs:
        if len(pending) < ceiling:
            pending.append(job)
        budget = ceiling - len(pending)      # a second read, after the append
        accepted += 1 if budget > 0 else 0
    return accepted, len(pending)


def after(jobs, ceiling):
    pending = []
    accepted = 0
    for job in jobs:
        size = len(pending)                  # hoisted: now stale below
        if size < ceiling:
            pending.append(job)
        budget = ceiling - size
        accepted += 1 if budget > 0 else 0
    return accepted, len(pending)


def cases():
    return [("fills-up",   lambda: (list(range(300_000)), 1_000)),
            ("never-full", lambda: (list(range(300_000)), 10**9)),
            ("edge",       lambda: ([], 4))]
