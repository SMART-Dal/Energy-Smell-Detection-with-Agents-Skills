"""C6.S3 Unnecessary Data Materialization -- the consumer can stop.

The card says a consumer that stops early is a real saving on top of the memory
one, because the elements after the stopping point are never computed. `hits-
early` is where that bites and `no-hit` is where the generator can only cost
its resumption, which is the same trade seen from the other side.
"""

def _expensive(x):
    total = 0
    for i in range(1, 12):
        total += (x * i) % 7
    return total


def before(values, target):
    return any(v for v in [_expensive(x) for x in values] if v == target)


def after(values, target):
    return any(_expensive(x) == target for x in values)


def cases():
    values = [i % 40 for i in range(200_000)]
    return [("hits-early", lambda: (list(values), _expensive(values[3]))),
            ("no-hit",     lambda: (list(values), -1)),
            ("edge",       lambda: ([], 1))]
