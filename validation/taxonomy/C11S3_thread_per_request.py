"""C11.S3 Unmanaged Thread Lifecycle -- one thread created per request against
a bounded pool.

The card says one thread at start-up is untidy and one per request accumulates,
so this measures the accumulation shape rather than the leak shape: creating
and joining a thread per unit of work against reusing four. Thread creation is
a real syscall and a stack allocation, which is what the repair removes.
"""

import threading
from concurrent.futures import ThreadPoolExecutor

WORKERS = 4


def _handle(n):
    total = 0
    for i in range(n):
        total += (i * 7919) % 10_007
    return total


def before(requests, work):
    results = [0] * requests

    def run(slot):
        results[slot] = _handle(work)

    for slot in range(requests):
        thread = threading.Thread(target=run, args=(slot,))
        thread.start()
        thread.join()
    return sum(results)


def after(requests, work):
    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(_handle, [work] * requests))


def cases():
    return [("many-requests", lambda: (2_000, 200)),
            ("few-requests",  lambda: (10, 200)),
            ("edge",          lambda: (0, 200))]
