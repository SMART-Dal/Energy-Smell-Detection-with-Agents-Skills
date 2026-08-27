"""C11.S1 Excessive Lock Contention -- narrowing the critical
section multiplies the number of acquisitions.

"Use fine-grained locks ... on overly broad critical sections" is the
description, and `C11S1_lock_contention` narrows one correctly: it moves a pure
computation out from under the lock, so the lock is held for less time and taken
exactly as often.

Narrowing usually gets read as "hold it for one operation at a time", and that
is what `after` does: one acquire and one release per update instead of one per
batch of a hundred. The critical section is now as short as it can be and the
lock is taken a hundred times as often, so the total lock traffic goes up by two
orders of magnitude. Under the GIL there was no parallelism to recover in
exchange.

There are two numbers in a contention finding and they move in opposite
directions: how long the lock is held, and how often it is taken. Narrowing that
keeps the second fixed is free; narrowing that raises it has to buy enough
concurrency to pay for the acquisitions, which CPU-bound Python cannot.
"""

import threading

THREADS = 4
BATCH = 100


def before(iterations):
    lock = threading.Lock()
    shared = [0]

    def worker():
        pending = 0
        for i in range(iterations):
            pending += i % 7
            if (i + 1) % BATCH == 0:
                with lock:                    # one acquisition per hundred
                    shared[0] += pending
                pending = 0
        with lock:
            shared[0] += pending

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return shared[0]


def after(iterations):
    lock = threading.Lock()
    shared = [0]

    def worker():
        for i in range(iterations):
            with lock:                        # "as narrow as possible"
                shared[0] += i % 7

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return shared[0]


def cases():
    return [("many-updates", lambda: (40_000,)),
            ("few-updates",  lambda: (400,)),
            ("edge",         lambda: (0,))]
