"""C11.S2 Forced Serial Bottleneck -- one lock serialising independent work.

Two things were wrong with the earlier version and both are fixed here. The
loop body was `_ = (i * 7919) % 10_007`, discarded, so the function computed
nothing and returned `True` -- there was no work for the lock to be serialising.
And `after` picked each thread's lock through an unsynchronised `counter[0] +=
1`, so which lock a thread got was itself a race.

Now each thread has a slot handed to it, accumulates into it, and the sums are
returned; the only difference between the variants is whether four threads
queue on one lock or take four.
"""

import threading

THREADS = 4


def _run(worker):
    partials = [0] * THREADS
    threads = [threading.Thread(target=worker, args=(slot, partials))
               for slot in range(THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sum(partials)


def before(n):
    lock = threading.Lock()

    def worker(slot, partials):
        total = 0
        for i in range(n):
            with lock:                      # one lock, and nothing is shared
                total += (i * 7919) % 10_007
        partials[slot] = total

    return _run(worker)


def after(n):
    locks = [threading.Lock() for _ in range(THREADS)]

    def worker(slot, partials):
        mine = locks[slot]                  # handed in, not raced for
        total = 0
        for i in range(n):
            with mine:
                total += (i * 7919) % 10_007
        partials[slot] = total

    return _run(worker)


def cases():
    return [("contended", lambda: (60_000,)),
            ("brief",     lambda: (200,)),
            ("edge",      lambda: (0,))]
