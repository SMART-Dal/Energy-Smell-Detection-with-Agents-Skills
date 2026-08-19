"""C7.S4 Inefficient Operation Order -- two bulk steps, deduplicate first.

The card separates this from C3.S6 by scope: here both operations are already
bulk steps and the repair swaps two statements. It also warns the cheap step
must still be cheap on the *full* input, so `all-unique` is the case where
hashing a million distinct values buys nothing and costs a pass.
"""

def _expensive(x):
    total = 0
    for i in range(1, 26):
        total += (x * i) % 13
    return total


def before(values):
    mapped = [_expensive(v) for v in values]
    return len(set(mapped))


def after(values):
    return len({_expensive(v) for v in set(values)})


def cases():
    return [("dense-duplicates", lambda: ([i % 97 for i in range(200_000)],)),
            ("all-unique",       lambda: (list(range(200_000)),)),
            ("edge",             lambda: ([],))]
