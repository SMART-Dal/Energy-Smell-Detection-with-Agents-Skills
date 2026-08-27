"""C11.S2 Forced Serial Bottleneck -- one resource per worker
means paying for the resource N times.

"A pipeline with many worker threads that all must acquire a single global
database connection" is the description's own example, and the named repair is
a pool -- one resource each, so nobody waits. `C11S2_pooled_resource` measures
that shape.

The resource here is expensive to construct and cheap to use, and each task
touches it briefly. Giving every worker its own means four constructions instead
of one, and the serial fraction it removed was a few microseconds of lock. The
contention was never the cost; the setup was.

The trade is construction cost against serial fraction. A pool pays when each
worker holds the resource for a large share of its time; where the hold is brief
-- or where the resource is a connection to something that is itself the
bottleneck -- more of them is more work and more load on the far end.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

WORKERS = 4


class Resource:
    """Expensive to build, cheap to use -- a parsed ruleset, a compiled model."""

    __slots__ = ("lock", "table")

    def __init__(self):
        self.lock = threading.Lock()
        self.table = {i: (i * 7919) % 10_007 for i in range(60_000)}

    def use(self, key):
        with self.lock:
            return self.table[key % 60_000]


def before(tasks):
    shared = Resource()
    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(shared.use, range(tasks)))


def after(tasks):
    local = threading.local()

    def run(key):
        if not hasattr(local, "resource"):
            local.resource = Resource()       # one construction per worker
        return local.resource.use(key)

    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(run, range(tasks)))


def cases():
    return [("brief-use", lambda: (2_000,)),
            ("heavy-use", lambda: (60_000,)),
            ("edge",      lambda: (0,))]
