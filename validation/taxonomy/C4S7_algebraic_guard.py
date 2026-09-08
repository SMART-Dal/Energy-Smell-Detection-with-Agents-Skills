"""C4.S7 Missing Edge-Case Guards -- the guard comes from a fact about the
arithmetic.

The card calls this the strongest form of the root cause and the one that needs
a reader rather than a rule: `is_prime` trial-divides, and parity settles half
the inputs in one modulo. The exception -- 2 is both even and prime -- is the
failure mode, so `all-even` carries it.
"""

def _is_prime(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def before(values):
    return [n for n in values if _is_prime(n)]


def after(values):
    return [n for n in values if n == 2 or (n % 2 == 1 and _is_prime(n))]


def cases():
    return [("mixed",    lambda: (list(range(2, 60_000)),)),
            ("all-even", lambda: (list(range(2, 60_000, 2)),))]
