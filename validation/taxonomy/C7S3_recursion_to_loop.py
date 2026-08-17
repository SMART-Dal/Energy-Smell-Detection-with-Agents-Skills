"""C7.S3 Avoidable Recursive Implementation -- linear recursion vs a loop.

From Javad's UnnecessaryRecursion/Factorial, which confirmed at +39.5%.
"""

def _fact_rec(n):
    if n <= 1:
        return 1
    return n * _fact_rec(n - 1)


def before(n, reps):
    total = 0
    for _ in range(reps):
        total += _fact_rec(n) % 7
    return total


def after(n, reps):
    total = 0
    for _ in range(reps):
        acc = 1
        for i in range(2, n + 1):
            acc *= i
        total += acc % 7
    return total


def cases():
    return [("deep", lambda: (300, 400)), ("shallow", lambda: (3, 400))]
