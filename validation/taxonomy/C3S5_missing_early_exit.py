"""C3.S5 Missing Loop Early Exit -- scanning past the answer.

The `hit-early` case is where the repair pays; `no-hit` is the adversarial one
where it can only cost, and both must be reported.
"""

def before(xs, target):
    found = False
    for x in xs:
        if x == target:
            found = True
    return found


def after(xs, target):
    for x in xs:
        if x == target:
            return True
    return False


def cases():
    return [("hit-early", lambda: (list(range(400_000)), 5)),
            ("no-hit", lambda: (list(range(400_000)), -1)),
            ("empty", lambda: ([], 1))]
