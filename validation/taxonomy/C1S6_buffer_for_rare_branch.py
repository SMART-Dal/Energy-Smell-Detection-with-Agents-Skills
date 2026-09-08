"""C1.S6 Unnecessary Initialization -- an N-element buffer for a flag that is
almost never set.

The card's second repair example. The conditional allocation costs one
comparison; the unconditional one costs an allocation and a zeroing pass per
call. `verbose=True` is the case that says what the guard costs when the branch
*is* taken.
"""

def before(rows, verbose=False):
    trace = [None] * len(rows)
    output = []
    for i, row in enumerate(rows):
        output.append(row * 2)
        if verbose:
            trace[i] = row
    return output, (trace if verbose else None)


def after(rows, verbose=False):
    trace = [None] * len(rows) if verbose else None
    output = []
    for i, row in enumerate(rows):
        output.append(row * 2)
        if verbose:
            trace[i] = row
    return output, trace


def cases():
    return [("quiet",   lambda: (list(range(200_000)), False)),
            ("verbose", lambda: (list(range(200_000)), True))]
