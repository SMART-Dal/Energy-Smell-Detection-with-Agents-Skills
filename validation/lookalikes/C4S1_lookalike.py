"""C4.S1 Poor Short-Circuit Ordering -- LOOKS THE SAME, IS NOT: the cheap operand is
the guard for the expensive one.

`expensive(x) and cheap(x)` becomes `cheap(x) and expensive(x)`, and
`C4S1_short_circuit_order` measures +92.3% when the cheap test rejects most
rows. The reordering is legal exactly when the two operands are independent.

They are not independent here. `row["profile"] is not None` is what makes
`row["profile"]["tier"]` safe to evaluate, so `and` is being used for control
flow and not only for a conjunction. Putting the expensive operand first makes
the profile lookup run on rows that have no profile.

The rule is narrower than "put the cheap test first": operands may be reordered
only when each of them is safe to evaluate on its own. A `None` check, an
`in` check before a subscript, and a length check before an index are all
guards wearing the shape of a cheap test.
"""

def _tier_rank(profile):
    return sum(ord(c) for c in profile["tier"]) % 7


def before(rows, wanted):
    return [r for r in rows if r["profile"] is not None and _tier_rank(r["profile"]) == wanted]


def after(rows, wanted):
    return [r for r in rows if _tier_rank(r["profile"]) == wanted and r["profile"] is not None]


def _rows(n, with_profile_ratio):
    step = max(1, int(1 / with_profile_ratio)) if with_profile_ratio else n + 1
    return [{"profile": {"tier": f"tier{i % 5}"} if i % step else None}
            for i in range(n)]


def cases():
    return [("some-missing", lambda: (_rows(200_000, 0.5), 3)),
            ("none-missing", lambda: ([{"profile": {"tier": f"tier{i % 5}"}}
                                       for i in range(200_000)], 3)),
            ("edge",         lambda: ([], 3))]
