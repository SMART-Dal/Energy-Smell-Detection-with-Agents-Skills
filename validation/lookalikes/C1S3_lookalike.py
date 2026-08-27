"""C1.S3 Redundant Control Flow -- LOOKS THE SAME, IS NOT: collapsing the branch
changes what the function returns.

`if condition: return True else: return False` collapses to `return condition`.
That is the textbook simplification, `C1S3_bool_branch` measures it at +6.1%,
and here it is wrong.

`_matching` returns `patterns.get(kind)` when the lookup succeeds, so the
"condition" is a list, not a bool. The branching version normalises it to
`True`/`False`; the collapsed version hands the caller the list. The caller
counts truthy results, so both agree on the count -- and then `sum` over the
returned values differs, because `True` is 1 and a list is not.

`return bool(condition)` is the correct collapse and costs a call, which is most
of what the branch cost in the first place. The rule is: collapse the branch
only when the condition is already a bool.
"""

_PATTERNS = {i: [i, i + 1] for i in range(0, 400, 2)}


def _matching_branching(kind):
    if _PATTERNS.get(kind):
        return True
    else:
        return False


def _matching_collapsed(kind):
    return _PATTERNS.get(kind)


def before(kinds):
    return [_matching_branching(kind) for kind in kinds]


def after(kinds):
    return [_matching_collapsed(kind) for kind in kinds]


def cases():
    return [("many-hits",   lambda: ([i % 400 for i in range(300_000)],)),
            ("many-misses", lambda: ([(i % 400) | 1 for i in range(300_000)],)),
            ("edge",        lambda: ([],))]
