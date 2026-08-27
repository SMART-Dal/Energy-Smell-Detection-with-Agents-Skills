"""C8.S3 Missing Local Lookup Caching -- LOOKS THE SAME, IS NOT: the loop is what
changes the attribute.

"Caching frequently accessed references in local variables before a loop
eliminates per-iteration lookup overhead" is the description, and
`C8S3_local_lookup_caching` measures the hoist at +55.2%.

The hoist is a promise that the chain resolves to the same object every time.
`limiter.threshold` is adjusted inside the loop -- that is what the limiter is
for -- so a local bound before the loop is a snapshot of the first iteration and
every later comparison uses a limit that has since moved.

The check is whether anything in the body can reach the names in the chain, and
it has to include indirect writes: a method call on the object, a callback, a
property with a setter, and anything the loop passes `self` to.
"""

class Limiter:
    __slots__ = ("threshold",)

    def __init__(self, threshold):
        self.threshold = threshold

    def tighten(self):
        self.threshold -= 1


class Context:
    __slots__ = ("limiter",)

    def __init__(self, threshold):
        self.limiter = Limiter(threshold)


def before(rows, threshold):
    context = Context(threshold)
    kept = 0
    for row in rows:
        if row % 1_000 == 0:
            context.limiter.tighten()
        if row < context.limiter.threshold:
            kept += 1
    return kept


def after(rows, threshold):
    context = Context(threshold)
    limit = context.limiter.threshold          # hoisted, and then stale
    kept = 0
    for row in rows:
        if row % 1_000 == 0:
            context.limiter.tighten()
        if row < limit:
            kept += 1
    return kept


def cases():
    return [("limit-moves", lambda: (list(range(300_000)), 150_000)),
            ("limit-still", lambda: ([i * 2 + 1 for i in range(300_000)], 150_000)),
            ("edge",        lambda: ([], 4))]
