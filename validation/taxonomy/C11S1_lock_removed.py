"""C11.S1 Excessive Lock Contention -- removing the synchronisation instead of
narrowing it.

The card's last suggestion: per-thread accumulators merged at the end need no
lock at all. This is a bigger edit than narrowing and should show more, so if
the narrowing cases read near zero and this one does not, the card can say
which repair to reach for.
"""

import threading

THREADS = 4


def before(n):
    lock = threading.Lock()
    shared = [0]

    def worker():
        for i in range(n):
            with lock:
                shared[0] += (i * 7919) % 10_007

    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return shared[0]


def after(n):
    partials = [0] * THREADS

    def worker(slot):
        total = 0
        for i in range(n):
            total += (i * 7919) % 10_007
        partials[slot] = total

    threads = [threading.Thread(target=worker, args=(s,)) for s in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sum(partials)


def cases():
    return [("contended", lambda: (60_000,)),
            ("brief",     lambda: (500,)),
            ("edge",      lambda: (0,))]
