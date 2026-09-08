"""C6.S1 Unnecessary Object Creation -- an intermediate nobody needed.

One list of N integers never built. The card attaches its own caveat from
C6.S3: for a *short* pipeline the materialised list can measure ahead of the
generator, because resumption costs more per element than the allocation saves.
So `short` is here to catch that rather than to confirm the long case.
"""

def before(names):
    lengths = [len(n) for n in names]
    return sum(lengths)


def after(names):
    return sum(len(n) for n in names)


def cases():
    return [("large",  lambda: ([f"name{i}" for i in range(1_000_000)],)),
            ("short",  lambda: ([f"name{i}" for i in range(30)],))]
