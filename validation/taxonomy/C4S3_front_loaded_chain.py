"""C4.S3 Inefficient Conditional Nesting -- a dispatch table
for a chain whose first arm answers almost everything.

The description recommends "dictionary-based dispatch" for a comparison chain,
and `C4S3_dispatch_table` measures a table against a four-way chain at +53.6%.
The table there replaced a chain whose arms were reached about equally often.

An `if/elif` chain costs one comparison for the arm it takes and none for the
arms below it. A dict dispatch costs a hash of the key, a probe, and -- because
the arms are functions -- a call and a frame, on every input including the ones
the chain settled first. Where the first arm takes 95% of the traffic, the chain
is doing one integer comparison per row and the table cannot get near it.

The precondition is the distribution, not the arm count. A table wins on a chain
that is long *and* whose matches are spread through it; on a chain that is long
and front-loaded it loses.
"""

def _bulk(value):
    return value * 2


def _sale(value):
    return value * 3


def _refund(value):
    return value * 5


def _adjustment(value):
    return value * 7


def _transfer(value):
    return value * 11


_HANDLERS = {0: _bulk, 1: _sale, 2: _refund, 3: _adjustment, 4: _transfer}


def before(rows):
    total = 0
    for kind, value in rows:
        if kind == 0:
            total += value * 2
        elif kind == 1:
            total += value * 3
        elif kind == 2:
            total += value * 5
        elif kind == 3:
            total += value * 7
        else:
            total += value * 11
    return total


def after(rows):
    total = 0
    for kind, value in rows:
        total += _HANDLERS[kind](value)
    return total


def _rows(n, first_arm_ratio):
    out = []
    step = max(1, int(1 / (1 - first_arm_ratio))) if first_arm_ratio < 1 else n + 1
    for i in range(n):
        out.append((0 if i % step else 1 + i % 4, i % 97))
    return out


def cases():
    return [("front-loaded", lambda: (_rows(300_000, 0.95),)),
            ("spread-out",   lambda: ([(i % 5, i % 97) for i in range(300_000)],)),
            ("edge",         lambda: ([],))]
