"""C7.S2 Inefficient Problem Decomposition -- exponential recursion vs memoised."""

def _fib_naive(n):
    if n < 2:
        return n
    return _fib_naive(n - 1) + _fib_naive(n - 2)


def _fib_memo(n, seen=None):
    if seen is None:
        seen = {}
    if n < 2:
        return n
    if n in seen:
        return seen[n]
    seen[n] = _fib_memo(n - 1, seen) + _fib_memo(n - 2, seen)
    return seen[n]


def before(n):
    return _fib_naive(n)


def after(n):
    return _fib_memo(n)


def cases():
    return [("deep", lambda: (24,)), ("shallow", lambda: (5,))]
