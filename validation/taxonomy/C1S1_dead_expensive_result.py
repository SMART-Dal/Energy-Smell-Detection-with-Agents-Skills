"""C1.S1 Dead Code -- an expensive result bound once per call and never read.

The other C1.S1 case puts the dead binding inside a loop. This one pays it once
per call, which is the shape the card says is the expensive kind: the binding
is one bytecode and the right-hand side is a full sort of the input.
"""

def _summarise(rows):
    return {"n": len(rows), "total": sum(rows)}


def before(rows):
    ordered = sorted(rows)               # built, bound, never read again
    summary = _summarise(rows)
    return summary["total"]


def after(rows):
    summary = _summarise(rows)
    return summary["total"]


def _scrambled(n):
    # Timsort is near-linear on sorted input, so a sorted list would understate
    # what the dead binding costs.
    return [(i * 7919) % n for i in range(n)]


def cases():
    return [("large",  lambda: (_scrambled(200_000),)),
            ("normal", lambda: (_scrambled(2_000),)),
            ("edge",   lambda: ([],))]
