"""C1.S2 Redundant Assignment -- assigning a value already held.

Advisory means the repair is real but too small to measure. This checks that.
"""

def before(xs):
    state = 0
    for x in xs:
        if x % 2:
            state = state          # leaves state unchanged
        else:
            state = x
    return state


def after(xs):
    state = 0
    for x in xs:
        if not x % 2:
            state = x
    return state


def cases():
    return [("large", lambda: (list(range(1_000_000)),)),
            ("small", lambda: (list(range(50)),))]
