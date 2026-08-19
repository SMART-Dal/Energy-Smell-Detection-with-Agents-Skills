"""C1.S5 Resultless Computation -- a loop where only the last pass is read.

Every iteration but the last computes a value that is immediately overwritten.
Valid only because `_score` is pure; the empty case has to be handled
explicitly, because the original raises `UnboundLocalError` and the repair
should raise the same thing.
"""

def _score(candidate, request):
    return sum(ord(c) for c in candidate) % (request + 1)


def before(candidates, request):
    for candidate in candidates:
        match = _score(candidate, request)
    return match


def after(candidates, request):
    if not candidates:
        raise UnboundLocalError(
            "local variable 'match' referenced before assignment")
    return _score(candidates[-1], request)


def cases():
    return [("large",  lambda: ([f"candidate-{i}" for i in range(200_000)], 97)),
            ("normal", lambda: ([f"candidate-{i}" for i in range(2_000)], 97)),
            ("edge",   lambda: (["only"], 97))]
