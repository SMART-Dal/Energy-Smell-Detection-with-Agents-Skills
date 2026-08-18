"""Cases for recursion_without_memo."""

import functools


def fib(n):
    # Two self-calls per level: the classic overlapping-subproblem tree.
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def count_paths(grid, row, column):
    # Two self-calls on separate lines is the same tree.
    if row == 0 or column == 0:
        return 1
    down = count_paths(grid, row - 1, column)
    across = count_paths(grid, row, column - 1)
    return down + across


def walk(node):
    # One self-call, but inside a loop, so the tree still branches.
    total = 1
    for child in node.children:
        total += walk(child)
    return total


@functools.cache
def cached_fib(n):
    # Already memoised.
    if n < 2:
        return n
    return cached_fib(n - 1) + cached_fib(n - 2)


@functools.lru_cache(maxsize=None)
def cached_paths(row, column):
    # The parameterised decorator counts too.
    if row == 0 or column == 0:
        return 1
    return cached_paths(row - 1, column) + cached_paths(row, column - 1)


def factorial(n):
    # Linear recursion: reported under a different kind, not this one.
    return 1 if n == 0 else n * factorial(n - 1)


def collect(node, out):
    # No self-call at all.
    for child in node.children:
        out.append(child)
    return out
