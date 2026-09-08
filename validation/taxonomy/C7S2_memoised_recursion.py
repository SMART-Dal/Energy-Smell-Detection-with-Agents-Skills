"""C7.S2 Suboptimal Problem Decomposition -- overlapping subproblems re-solved.

The card's first named failure, and the one that turns naive Fibonacci from
linear into exponential. It asks for evidence that subproblems really do
repeat, so `no-overlap` is a tree walk where each node is visited once and the
memo is pure overhead -- which is the card's first `NOT a smell when` clause.
"""

def _fib_naive(n):
    if n < 2:
        return n
    return _fib_naive(n - 1) + _fib_naive(n - 2)


def _fib_memo(n, memo=None):
    if memo is None:
        memo = {}
    if n < 2:
        return n
    if n not in memo:
        memo[n] = _fib_memo(n - 1, memo) + _fib_memo(n - 2, memo)
    return memo[n]


def _sum_tree_naive(depth):
    if depth == 0:
        return 1
    return depth + _sum_tree_naive(depth - 1)


def _sum_tree_memo(depth, memo=None):
    if memo is None:
        memo = {}
    if depth == 0:
        return 1
    if depth not in memo:
        memo[depth] = depth + _sum_tree_memo(depth - 1, memo)
    return memo[depth]


def before(n, kind):
    return _fib_naive(n) if kind == "overlap" else _sum_tree_naive(n)


def after(n, kind):
    return _fib_memo(n) if kind == "overlap" else _sum_tree_memo(n)


def cases():
    return [("overlap",    lambda: (26, "overlap")),
            ("no-overlap", lambda: (400, "chain"))]
