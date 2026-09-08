"""C6.S7 Leaking Mutable Default Arguments -- the sharing is the
cache.

`def f(x, memo={})` is the classic defect and the description gives the repair
verbatim: `None` as the default and the object built inside the body. Applied to
an accumulator that leaks state between unrelated callers, it is right.

The default here is a memo, and it is shared on purpose -- it is the oldest
Python idiom for a per-function cache, older than `functools.lru_cache`. The
mechanical repair gives every call its own empty dict, so the memo never
survives a call and every input is computed from scratch. The result is
identical and the work is the whole point of the code.

The two are told apart by what the default is read for. A default that is
*appended to* and returned leaks the caller's data into the next caller; a
default that is only probed and filled is a cache. The second still deserves a
comment and probably deserves `lru_cache`, but not this repair.
"""

def _cost(n):
    total = 0
    for i in range(1, 90):
        total += (n * i) % 17
    return total


def _shared_memo(values, memo={}):
    total = 0
    for value in values:
        hit = memo.get(value)
        if hit is None:
            hit = memo[value] = _cost(value)
        total += hit
    return total


def _fresh_memo(values, memo=None):
    if memo is None:
        memo = {}
    total = 0
    for value in values:
        hit = memo.get(value)
        if hit is None:
            hit = memo[value] = _cost(value)
        total += hit
    return total


def before(batches):
    return sum(_shared_memo(batch) for batch in batches)


def after(batches):
    return sum(_fresh_memo(batch) for batch in batches)


def cases():
    batch = [i % 300 for i in range(2_000)]
    return [("repeated-batches", lambda: ([list(batch) for _ in range(20)],)),
            ("distinct-batches", lambda: ([[i * 2_000 + j for j in range(2_000)]
                                           for i in range(20)],))]
