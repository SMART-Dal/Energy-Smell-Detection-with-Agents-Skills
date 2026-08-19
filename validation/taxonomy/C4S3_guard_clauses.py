"""C4.S3 Deep Conditional Nesting -- flattening with guard clauses.

The adversarial half. The card says this form evaluates the same tests the same
number of times and should measure as nothing, so a reading near zero here
confirms the card rather than refuting the root cause -- and tells the agent to
report the flattening as a readability change with no energy claim attached.
"""

def _work(request):
    return request["size"] * 2


def before(requests):
    total = 0
    for request in requests:
        if request is not None:
            if request["ready"]:
                if request["size"] > 0:
                    total += _work(request)
    return total


def after(requests):
    total = 0
    for request in requests:
        if request is None:
            continue
        if not request["ready"]:
            continue
        if request["size"] <= 0:
            continue
        total += _work(request)
    return total


def _requests(n):
    return [None if i % 5 == 0 else {"ready": i % 3 != 0, "size": i % 7}
            for i in range(n)]


def cases():
    return [("large",  lambda: (_requests(500_000),)),
            ("normal", lambda: (_requests(5_000),)),
            ("edge",   lambda: ([],))]
