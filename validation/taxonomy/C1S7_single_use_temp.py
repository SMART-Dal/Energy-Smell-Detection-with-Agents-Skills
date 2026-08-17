"""C1.S7 Unnecessary Variable -- marked advisory, and this checks that.

`advisory_only` is a claim in its own right: that the repair is real but too
small for any workload to lift above the noise floor. If a saving shows up
here, the classification is wrong and the root cause should be measured like
any other.
"""


def before(xs):
    total = 0
    for x in xs:
        value = x * 2 + 1
        total += value
    return total


def after(xs):
    total = 0
    for x in xs:
        total += x * 2 + 1
    return total


def cases():
    return [
        ("large", lambda: (list(range(1_000_000)),)),
        ("small", lambda: (list(range(50)),)),
    ]
