"""C7.S2 Suboptimal Problem Decomposition -- a branch ruled out before
descending.

The card's second named failure. The bound has to be *sound* -- no pruned
branch could have held a better answer -- and here it is: the values are
non-negative, so a partial sum already over the target can only grow. `loose-
bound` sets the target high enough that almost nothing prunes, which is the
card's "the search space is small enough" clause seen from the other side.
"""

def _search_all(values, index, running, target, hits):
    if index == len(values):
        return hits + (1 if running == target else 0)
    hits = _search_all(values, index + 1, running + values[index], target, hits)
    return _search_all(values, index + 1, running, target, hits)


def _search_pruned(values, index, running, target, hits):
    if running > target:
        return hits                       # sound: the values are non-negative
    if index == len(values):
        return hits + (1 if running == target else 0)
    hits = _search_pruned(values, index + 1, running + values[index], target, hits)
    return _search_pruned(values, index + 1, running, target, hits)


def before(values, target):
    return _search_all(values, 0, 0, target, 0)


def after(values, target):
    return _search_pruned(values, 0, 0, target, 0)


def cases():
    values = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67]
    return [("tight-bound", lambda: (list(values), 30)),
            ("loose-bound", lambda: (list(values), 10_000)),
            ("edge",        lambda: ([3], 3))]
