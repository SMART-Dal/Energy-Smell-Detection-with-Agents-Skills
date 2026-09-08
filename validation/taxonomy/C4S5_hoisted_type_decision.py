"""C4.S5 Expensive Comparison -- hoisting the type decision out of the loop.

The card's *other* repair, and the one it warns about: the hoisted version pays
a full extra pass to buy a branch-free loop, so it wins only when the loop body
is heavier than the check. `heavy-body` and `light-body` put that on either
side of the line, which is the only way the card can say where the line is.
"""

def before(values, work):
    out = []
    for value in values:
        if isinstance(value, str):
            out.append(value.strip() * work)
        else:
            out.append(str(value) * work)
    return out


def after(values, work):
    if values and all(type(v) is str for v in values):
        return [v.strip() * work for v in values]
    return [v.strip() * work if isinstance(v, str) else str(v) * work for v in values]


def cases():
    homogeneous = [f" s{i} " for i in range(120_000)]
    return [("heavy-body", lambda: (list(homogeneous), 40)),
            ("light-body", lambda: (list(homogeneous), 1))]
