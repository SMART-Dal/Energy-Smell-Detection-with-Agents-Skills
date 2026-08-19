"""C1.S5 Resultless Computation -- a pipeline stage the next stage ignores.

The card's flagship example and the form it says actually matters: softmax is
strictly monotonic, so it preserves the position of the maximum, and a function
that returns only that position never needed the exponentials. Every line looks
purposeful, which is why this form leaves no syntactic trace.

Note the initial value has to change from 0 to -inf: logits can be negative
where probabilities cannot, and without that the repair is silently wrong on
all-negative input -- which the `all-negative` case exists to catch.
"""

import math


def _softmax(logits):
    exponentials = [math.exp(v) for v in logits]
    total = sum(exponentials)
    return [e / total for e in exponentials]


def before(logits):
    probabilities = _softmax(logits)
    best, index = float("-inf"), 0
    for i, p in enumerate(probabilities):
        if p > best:
            best, index = p, i
    return index


def after(logits):
    best, index = float("-inf"), 0
    for i, value in enumerate(logits):
        if value > best:
            best, index = value, i
    return index


def cases():
    return [("large",        lambda: ([(i * 7919) % 500 / 100.0 for i in range(300_000)],)),
            ("normal",       lambda: ([(i * 7919) % 500 / 100.0 for i in range(3_000)],)),
            ("all-negative", lambda: ([-1.0 - (i % 7) for i in range(1_000)],))]
