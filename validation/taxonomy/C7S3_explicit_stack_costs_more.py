"""C7.S3 Avoidable Recursive Implementation -- the explicit
stack is slower than the call stack.

"Implementing tree traversal recursively when an explicit stack-based iteration
would avoid frame overhead for deep trees" is the description, and
`C7S3_recursion_to_loop` measures the conversion at +54.4% on a linear chain
that recurses thousands deep.

The tree here is eight levels deep. CPython's frames are objects it allocates
from a free list and reuses, and a recursive call is one `CALL` and one `RETURN`;
the manual version replaces that with a Python `list`, an `append`, a `pop`, a
tuple to carry the state and a `while` test per node. The C-level machinery it
removed was cheaper than the Python-level machinery it added.

The description's own condition is "problems with deep recursion". Depth is what
makes recursion expensive -- frames held simultaneously, and the 1000-frame
limit. A shallow, wide traversal is the case where the recursive form is both
shorter and faster.
"""

import sys

sys.setrecursionlimit(10_000)


def _node(depth, fanout, value):
    if depth == 0:
        return (value, ())
    return (value, tuple(_node(depth - 1, fanout, value * 2 + i)
                         for i in range(fanout)))


def _sum_recursive(node):
    value, children = node
    total = value
    for child in children:
        total += _sum_recursive(child)
    return total


def _sum_iterative(node):
    total = 0
    stack = [node]
    while stack:
        value, children = stack.pop()
        total += value
        for child in children:
            stack.append(child)
    return total


def before(tree):
    return _sum_recursive(tree)


def after(tree):
    return _sum_iterative(tree)


_SHALLOW_WIDE = _node(7, 4, 1)          # 21_845 nodes, 8 levels
_DEEP_NARROW = _node(900, 1, 1)         # 901 nodes, 901 levels


def cases():
    return [("shallow-and-wide", lambda: (_SHALLOW_WIDE,)),
            ("deep-and-narrow",  lambda: (_DEEP_NARROW,)),
            ("edge",             lambda: ((1, ()),))]
