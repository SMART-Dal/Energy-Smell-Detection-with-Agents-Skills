"""C3.S5 Missing Loop Early Exit -- filtering everything, then slicing.

The card's second repair example, and the one place it says writing the loop
out beats the comprehension. `limit-small` is where stopping early skips most
of the collection; `limit-large` asks for nearly all of it, so the explicit
loop can only cost its extra bookkeeping.
"""

from itertools import islice


def before(values, limit, floor):
    return [x for x in values if x > floor][:limit]


def after(values, limit, floor):
    return list(islice((x for x in values if x > floor), limit))


def cases():
    values = [(i * 7919) % 100_000 for i in range(400_000)]
    return [("limit-small", lambda: (list(values), 20, 10)),
            ("limit-large", lambda: (list(values), 350_000, 10))]
