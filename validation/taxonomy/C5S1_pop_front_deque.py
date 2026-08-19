"""C5.S1 Inefficient Data Structure Choice -- the operation is not membership.

The card's third repair example, and the reason it asks which operation the hot
path performs before judging the container: `list.pop(0)` moves every remaining
element down a slot, so draining a list this way is quadratic in its length,
where a `deque` pops from either end in constant time. Same root cause,
different operation, and a rule matching on `in` would never see it.
"""

from collections import deque


def before(pending):
    order = []
    while pending:
        order.append(pending.pop(0))
    return len(order)


def after(pending):
    queue = deque(pending)
    order = []
    while queue:
        order.append(queue.popleft())
    return len(order)


def cases():
    return [("large",  lambda: (list(range(60_000)),)),
            ("normal", lambda: (list(range(600)),)),
            ("edge",   lambda: ([],))]
