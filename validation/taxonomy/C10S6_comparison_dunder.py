"""C10.S6 Operator Overloading Overhead -- a comparison dunder on the hot path.

Both other measured files in this root cause overload arithmetic, which the
loop invokes directly. A comparison dunder is reached differently: `min` calls
it through the comparison protocol, once per element, and each call is a Python
frame where the repair's `key` is one attribute read and a primitive compare
in C.

The original also slices `events[1:]`, copying the whole list before it starts
-- a second saving in the same edit, which the card names so the reader knows
the reading is not attributable to the dunder alone.
"""


class Event:
    __slots__ = ("timestamp", "name")

    def __init__(self, timestamp, name):
        self.timestamp = timestamp
        self.name = name

    def __lt__(self, other):
        return self.timestamp < other.timestamp


def before(events):
    best = events[0]
    for event in events[1:]:
        if event < best:
            best = event
    return best.name


def after(events):
    return min(events, key=lambda e: e.timestamp).name


def _events(n):
    return [Event((i * 7919) % 1_000_003, f"e{i}") for i in range(n)]


def cases():
    return [("many",   lambda: (_events(300_000),)),
            ("normal", lambda: (_events(3_000),))]
