"""C4.S1 Suboptimal Condition Order -- the expensive operand builds a set.

The card's second example: the operand that does work need not be a bare call.
`retryable_statuses` builds a set per evaluation, and on the last attempt the
comparison alone settles the question so the set is never built.
"""

class Policy:
    __slots__ = ("max_attempts",)

    def __init__(self, max_attempts):
        self.max_attempts = max_attempts

    def retryable_statuses(self, host):
        return {c for c in range(500, 600) if (c + len(host)) % 2 == 0}


def before(responses, policy):
    return sum(
        1 for status, host, attempt in responses
        if status in policy.retryable_statuses(host) and attempt < policy.max_attempts
    )


def after(responses, policy):
    return sum(
        1 for status, host, attempt in responses
        if attempt < policy.max_attempts and status in policy.retryable_statuses(host)
    )


def _responses(n, exhausted_ratio):
    return [(500 + i % 100, f"host{i % 8}", 9 if (i % 100) < exhausted_ratio * 100 else 0)
            for i in range(n)]


def cases():
    return [("mostly-exhausted", lambda: (_responses(60_000, 0.9), Policy(3))),
            ("mostly-retrying",  lambda: (_responses(60_000, 0.0), Policy(3)))]
