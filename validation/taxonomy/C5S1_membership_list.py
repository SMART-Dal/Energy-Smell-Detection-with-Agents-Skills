"""C5.S1 -- linear membership testing against a set.

The least controversial claim in the taxonomy: `x in list` is O(n) and `x in
set` is O(1). Included precisely because it should confirm easily -- a suite
where nothing confirms is measuring the harness, not the taxonomy.

The `hits-early` case is the honest adversarial one: when the target is always
at the front of the list, the linear scan wins and the repair is a regression.
"""


def before(haystack, needles):
    return [n for n in needles if n in haystack]


def after(haystack, needles):
    lookup = set(haystack)
    return [n for n in needles if n in lookup]


def cases():
    return [
        ("hits-late", lambda: (list(range(5_000)), list(range(0, 5_000, 5)))),
        ("hits-early", lambda: (list(range(5_000)), [1] * 1_000)),
    ]
