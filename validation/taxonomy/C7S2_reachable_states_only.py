"""C7.S2 Inefficient Problem Decomposition -- an iterative DP that solves states
nothing can reach.

No recursion anywhere. The decomposition is a subset-sum table over
`0..target`, and `before` sweeps the whole row for every coin because that is
how the textbook loop is written. Most of that row is unreachable: after k
coins nothing above `sum(coins[:k])` can be marked, so the sweep is re-deciding
"still False" for states no coin has been able to reach yet.

`after` keeps the identical table and the identical recurrence and only narrows
the sweep to the reachable prefix. Same subproblems, same answers, fewer of
them attempted -- which is what "solving subproblems that cannot affect the
final output" means when the solver is a loop rather than a call tree.

`dense-coins` is the case where the bound buys nothing: the coins are small
enough that the reachable prefix is the whole row after the second coin, so the
extra bookkeeping is all the change does.
"""

def before(coins, target):
    reachable = [False] * (target + 1)
    reachable[0] = True
    for coin in coins:
        for value in range(target, coin - 1, -1):
            if reachable[value - coin]:
                reachable[value] = True
    return sum(reachable)


def after(coins, target):
    reachable = [False] * (target + 1)
    reachable[0] = True
    highest = 0                       # nothing above this has been reached yet
    for coin in coins:
        top = min(target, highest + coin)
        for value in range(top, coin - 1, -1):
            if reachable[value - coin]:
                reachable[value] = True
        highest = top
    return sum(reachable)


def cases():
    return [("sparse-coins", lambda: ([997, 991, 983, 977, 971, 967], 40_000)),
            ("dense-coins",  lambda: ([1, 2, 3, 4, 5, 6, 7, 8], 40_000)),
            ("edge",         lambda: ([5], 5))]
