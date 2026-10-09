"""C7.S3 Unnecessary Recursion -- a recursion with two self-calls per frame.

The card's first `NOT a smell when` clause: a recursion with two self-calls is
a tree walk, and replacing it with an explicit stack reimplements the call
stack in slower Python. `before` is the recursion and `after` is the explicit
stack, so a negative reading is the card being right -- and it is the reading
that stops an agent applying C7.S3 to every recursion it meets.
"""

class Node:
    __slots__ = ("value", "left", "right")

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def _build(depth, seed=1):
    if depth == 0:
        return None
    return Node(seed, _build(depth - 1, seed * 2), _build(depth - 1, seed * 2 + 1))


_TREE = _build(16)


def _sum_recursive(node):
    if node is None:
        return 0
    return node.value + _sum_recursive(node.left) + _sum_recursive(node.right)


def _sum_stack(node):
    total = 0
    stack = [node]
    while stack:
        current = stack.pop()
        if current is None:
            continue
        total += current.value
        stack.append(current.left)
        stack.append(current.right)
    return total


def before(repeats):
    return sum(_sum_recursive(_TREE) for _ in range(repeats))


def after(repeats):
    return sum(_sum_stack(_TREE) for _ in range(repeats))


def cases():
    return [("many-walks", lambda: (12,)),
            ("one-walk",   lambda: (1,)),
            ("edge",       lambda: (1,))]
