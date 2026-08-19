"""C7.S3 Unnecessary Recursion -- a linear recursion with an accumulator loop.

The card's precondition is that the recursion is *linear*: exactly one self-call
on each path, so it is sequencing rather than branching. The saving is the
frame cost times the depth, so `shallow` is the case where three levels save
three frames and there is no finding.
"""

def _factorial_recursive(n):
    if n <= 1:
        return 1
    return n * _factorial_recursive(n - 1)


def _factorial_iterative(n):
    total = 1
    for i in range(2, n + 1):
        total *= i
    return total


def before(n, repeats):
    return sum(_factorial_recursive(n) % 1_000_003 for _ in range(repeats))


def after(n, repeats):
    return sum(_factorial_iterative(n) % 1_000_003 for _ in range(repeats))


def cases():
    return [("deep",    lambda: (900, 400)),
            ("shallow", lambda: (3, 200_000)),
            ("edge",    lambda: (1, 10))]
