"""C11.S1 Excessive Lock Contention -- the lock held across the whole loop body.

Threads make this noisy, so the deciding case is deliberately large.
"""

import threading


def _run(worker, n):
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return n


def before(n):
    lock = threading.Lock()
    shared = [0]

    def worker():
        for i in range(n):
            with lock:
                value = (i * 7919) % 10_007      # computed inside the lock
                shared[0] += value
    return _run(worker, n)


def after(n):
    lock = threading.Lock()
    shared = [0]

    def worker():
        for i in range(n):
            value = (i * 7919) % 10_007          # computed outside
            with lock:
                shared[0] += value
    return _run(worker, n)


def cases():
    return [("contended", lambda: (60_000,)), ("brief", lambda: (200,))]
