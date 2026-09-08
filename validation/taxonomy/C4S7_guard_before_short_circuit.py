"""C4.S7 Missing Edge-Case Guards -- a guard in front of something that already
short-circuits.

The card's second `NOT a smell when` clause and the reason most candidates for
this root cause die: `sorted()` on an empty or single-element list is already
close to free, so the guard adds a test to every call and saves almost nothing.
Expected to read at or below zero, which is the useful answer.
"""

def before(batches):
    return [sorted(b) for b in batches]


def after(batches):
    out = []
    for b in batches:
        if len(b) < 2:
            out.append(list(b))
        else:
            out.append(sorted(b))
    return out


def cases():
    return [("mostly-trivial", lambda: ([[] if i % 2 else [i] for i in range(400_000)],)),
            ("mostly-real",    lambda: ([[3, 1, 2, i] for i in range(200_000)],))]
