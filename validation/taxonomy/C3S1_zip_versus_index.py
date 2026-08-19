"""C3.S1 Suboptimal Iteration Construct -- two sequences walked by a shared
index.

The card's second repair example. `zip` advances both iterators in C where the
index form builds a range, boxes each index and does two bounds-checked
subscripts. The behaviour change it names is real and checked here: `zip` stops
at the shorter sequence where the original raises `IndexError`, so `ragged`
keeps the lengths equal and the difference stays a performance one.
"""

def before(first, second):
    return sum([abs(first[i] - second[i]) for i in range(len(first))])


def after(first, second):
    return sum([abs(a - b) for a, b in zip(first, second)])


def cases():
    return [("large",  lambda: (list(range(600_000)), list(range(600_000, 0, -1)))),
            ("normal", lambda: (list(range(6_000)), list(range(6_000, 0, -1)))),
            ("edge",   lambda: ([], []))]
