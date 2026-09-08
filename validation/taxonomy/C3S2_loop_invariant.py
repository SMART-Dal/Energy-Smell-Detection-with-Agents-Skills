"""C3.S2 Loop-Invariant Computation -- hoisting work that cannot change.

The analyzer behind this (`loop_invariant_expression`) is the one with no
linter equivalent, so it carries a lot of the suite's weight and needs to be
right.
"""


def before(rows, config):
    out = []
    for row in rows:
        limit = len(config) * 2
        out.append(row + limit)
    return out


def after(rows, config):
    limit = len(config) * 2
    out = []
    for row in rows:
        out.append(row + limit)
    return out


def cases():
    return [
        ("large", lambda: (list(range(300_000)), list(range(64)))),
        ("small", lambda: (list(range(50)), list(range(64)))),
    ]
