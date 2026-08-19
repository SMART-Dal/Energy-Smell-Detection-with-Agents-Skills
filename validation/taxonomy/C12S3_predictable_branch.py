"""C12.S3 Unpredictable Branches -- the branch is already predictable.

The card's second `NOT a smell when` clause: "unpredictable" means close to a
coin toss, not merely data-dependent. Here the condition takes long runs of one
outcome, which any predictor learns, so the branchless rewrite can only cost
its extra arithmetic. Same edit as the case that lost by 34%; this one says
whether the *predictability* was carrying any of that.
"""

def before(values):
    total = 0
    for x in values:
        if x > 0:
            total += x
    return total


def after(values):
    total = 0
    for x in values:
        total += x * (x > 0)
    return total


def cases():
    n = 300_000
    return [("long-runs",  lambda: ([(1 if (i // 1000) % 2 else -1) * (i % 97) for i in range(n)],)),
            ("all-taken",  lambda: (list(range(1, n)),)),
            ("edge",       lambda: ([],))]
