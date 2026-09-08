"""C8.S1 Missing Memoization Cache -- LOOKS THE SAME, IS NOT: the function is not pure.

"Use functools.lru_cache for pure functions" is the description, and
`C8S1_memoization` measures a memo over a genuinely deterministic predicate at
+89.4%. The key characteristic the description names first is determinism.

`_rate` reads a table that the loop updates. Its arguments do not change between
the call that returns 3 and the call that returns 7, so a memo keyed on the
arguments returns the first answer forever. Nothing raises and the totals are
plausible; they are just computed from a rate that was correct at some earlier
point in the loop.

The test is every name the body reads, not just its parameters. A function that
touches a module global, an instance attribute, the clock, a file, or anything
another thread writes is not memoisable on its arguments alone.
"""

_RATES = {}


def _rate(currency):
    return _RATES[currency]                  # depends on state, not arguments


def before(rows):
    _RATES.clear()
    _RATES.update({f"cur{i}": 1 + i for i in range(20)})
    total = 0
    for step, (currency, amount) in enumerate(rows):
        if step % 5_000 == 0:
            _RATES[currency] = _RATES[currency] + 1     # the rate moves
        total += amount * _rate(currency)
    return total


def after(rows):
    _RATES.clear()
    _RATES.update({f"cur{i}": 1 + i for i in range(20)})
    memo = {}
    total = 0
    for step, (currency, amount) in enumerate(rows):
        if step % 5_000 == 0:
            _RATES[currency] = _RATES[currency] + 1
        hit = memo.get(currency)
        if hit is None:
            hit = memo[currency] = _rate(currency)      # frozen at first sight
        total += amount * hit
    return total


def cases():
    rows = [(f"cur{i % 20}", i % 97) for i in range(200_000)]
    return [("rates-move",  lambda: (list(rows),)),
            ("rates-still", lambda: ([(f"cur{i % 20}", i % 97) for i in range(4_999)],))]
