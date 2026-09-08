"""C1.S3 Redundant Control Flow -- a condition guarding nothing.

An attribute read and a jump per element. The card calls this two instructions;
this is where that gets a number. The `strict` flag is read but never acted on,
which is the shape a version-history check is supposed to catch.
"""

class Sink:
    __slots__ = ("strict", "seen")

    def __init__(self, strict):
        self.strict = strict
        self.seen = 0


def before(sink, values):
    for value in values:
        if sink.strict:
            pass
        sink.seen += value
    return sink.seen


def after(sink, values):
    for value in values:
        sink.seen += value
    return sink.seen


def cases():
    return [("large",  lambda: (Sink(True), list(range(500_000)))),
            ("normal", lambda: (Sink(True), list(range(5_000))))]
