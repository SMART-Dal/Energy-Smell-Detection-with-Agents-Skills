"""C11.S2 Forced Serial Bottleneck -- one shared resource against a pool of
them.

The card's first named repair. Every worker needs the resource for a
substantial share of its time, which is the precondition, and the pool gives
each one its own. `brief-use` is the adversarial case: the same structure where
the resource is touched briefly, so the serial fraction is small and the pool
should buy nothing.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

WORKERS = 4


class Resource:
    __slots__ = ("lock",)

    def __init__(self):
        self.lock = threading.Lock()

    def use(self, n):
        with self.lock:
            total = 0
            for i in range(n):
                total += (i * 7919) % 10_007
            return total


def before(tasks, work):
    shared = Resource()
    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(lambda _: shared.use(work), range(tasks)))


def after(tasks, work):
    local = threading.local()

    def run(_):
        if not hasattr(local, "resource"):
            local.resource = Resource()
        return local.resource.use(work)

    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(run, range(tasks)))


def cases():
    return [("heavy-use", lambda: (200, 4_000)),
            ("brief-use", lambda: (200, 5)),
            ("edge",      lambda: (0, 10))]
