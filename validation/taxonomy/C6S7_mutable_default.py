"""C6.S7 Leaking Mutable Default Arguments -- what the standard repair costs.

The previous version of this file had `acc=None` and the `if acc is None`
guard in *both* variants: two byte-identical helpers behind two different
names. It read -0.7%, which was the measurement of nothing.

The obstacle it was working around is real and is the card's own point: on a
default that genuinely accumulates, `before` and `after` do not return the same
answers, so a paired comparison cannot be built at all. What can be measured is
the case where the default is mutated and then reset -- a scratch buffer, which
is the one shape where the leak does not happen and the repair is therefore
equivalent. Both variants return the same list every time; only the allocation
differs.

That makes this the price of the repair rather than the price of the defect:
`before` reuses one list and clears it, `after` builds a fresh one per call. If
the reading is a loss, the card can say that the repair is a correctness change
with an energy cost, which is a more honest thing to tell an agent than
implying it saves something.
"""

def _shared_scratch(row, scratch=[]):
    scratch.clear()                      # reset, so nothing leaks between calls
    for i in range(row % 8):
        scratch.append(row + i)
    return len(scratch)


def _fresh_scratch(row, scratch=None):
    if scratch is None:
        scratch = []
    for i in range(row % 8):
        scratch.append(row + i)
    return len(scratch)


def before(rows):
    return sum(_shared_scratch(row) for row in rows)


def after(rows):
    return sum(_fresh_scratch(row) for row in rows)


def cases():
    return [("many-calls", lambda: (list(range(400_000)),)),
            ("few-calls",  lambda: (list(range(40)),)),
            ("edge",       lambda: ([],))]
