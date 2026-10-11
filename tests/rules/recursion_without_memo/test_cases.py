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


def merge_sort(items):
    # Divide and conquer: the halves are disjoint, so nothing is ever recomputed.
    if len(items) <= 1:
        return items
    half = len(items) // 2
    left = merge_sort(items[:half])
    right = merge_sort(items[half:])
    return merge(left, right)


def tree_depth(node):
    # Two children, each visited once: a cache would never be read.
    if node is None:
        return 0
    return 1 + max(tree_depth(node.left), tree_depth(node.right))


def fib_memo(n, memo={}):
    # Already memoized, just not with a decorator.
    if n <= 1:
        return n
    if n not in memo:
        memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]


class Solver:
    def fib(self, n):
        # `self.fib(...)` is the same recursion as `fib(...)`, and matching only
        # bare names left the rule blind to anything written as a method.
        if n < 2:
            return n
        return self.fib(n - 1) + self.fib(n - 2)


def quicksort(arr, low, high):
    # The same container to both calls, split at a pivot computed in the body.
    # Neither branch crosses `p`, so nothing is recomputed -- and `lru_cache`
    # could not key on the list anyway. `count_paths` beside it offsets its own
    # parameters instead, and those branches do converge.
    if low < high:
        p = partition(arr, low, high)
        quicksort(arr, low, p - 1)
        quicksort(arr, p + 1, high)


class PortFinder:
    def find_available_port(self, start):
        # A method delegating to the module-level function of the same name:
        # inside a method a bare name is never the method itself.
        return find_available_port(self.host, start)
