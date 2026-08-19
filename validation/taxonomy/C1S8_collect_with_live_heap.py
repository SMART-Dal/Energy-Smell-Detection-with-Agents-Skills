"""C1.S8 Excessive Runtime-Management Calls -- `gc.collect()` against a heap
that is actually large.

The other C1.S8 case collects inside a loop with almost nothing alive. The card
claims the cost scales with the *live heap* as well as the call count, so this
one holds a large graph of tracked objects alive across the loop. If the two
readings differ, the card can say by how much.
"""

import gc


class Node:
    __slots__ = ("value", "peer")

    def __init__(self, value):
        self.value = value
        self.peer = None


def _graph(n):
    nodes = [Node(i) for i in range(n)]
    for i, node in enumerate(nodes):
        node.peer = nodes[(i + 1) % n]
    return nodes


def before(batches, heap):
    total = 0
    for batch in batches:
        total += sum(batch)
        gc.collect()
    return total + len(heap)


def after(batches, heap):
    total = 0
    for batch in batches:
        total += sum(batch)
    return total + len(heap)


def cases():
    return [("big-heap",   lambda: ([[1, 2, 3]] * 40, _graph(200_000))),
            ("small-heap", lambda: ([[1, 2, 3]] * 40, _graph(200))),
            ("edge",       lambda: ([], _graph(200)))]
