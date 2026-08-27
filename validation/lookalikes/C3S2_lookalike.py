"""C3.S2 Recomputing Loop-Invariant Values -- LOOKS THE SAME, IS NOT: the expression is
loop-invariant and its value is not.

`len(out)` appears in the loop body with no argument that the loop changes --
except that `out` is what the loop is building. The expression is textually
constant, so a rule that hoists constant sub-expressions hoists it, and
`C3S2_loop_invariant` shows what that is worth when the hoist is legal: +45%.

Hoisted, `capacity` is computed against an empty list and never rises, so every
row after the first is measured against the wrong threshold.

Invariance is a property of the values, not of the text. The check is whether
any statement in the body can reach the names the expression reads -- and a
container being appended to is the case that gets missed, because the append
does not mention the expression at all.
"""

def before(rows, ceiling):
    out = []
    for row in rows:
        capacity = ceiling - len(out)          # changes as `out` grows
        if capacity > 0:
            out.append(row)
    return out


def after(rows, ceiling):
    out = []
    capacity = ceiling - len(out)              # hoisted: evaluated once, empty
    for row in rows:
        if capacity > 0:
            out.append(row)
    return out


def cases():
    return [("fills-up",   lambda: (list(range(200_000)), 5_000)),
            ("never-full", lambda: (list(range(200_000)), 10**9)),
            ("edge",       lambda: ([], 4))]
