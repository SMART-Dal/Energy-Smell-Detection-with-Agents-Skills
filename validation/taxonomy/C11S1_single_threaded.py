"""C11.S1 Excessive Lock Contention -- the same narrowing, with one thread.

The card's second `NOT a smell when` clause: a lock reached by one thread costs
its uncontended acquisition and nothing else, so narrowing the critical section
has nothing to buy. The other C11.S1 case runs four threads and read +0.2%;
this one removes the threads entirely, so any difference between the two
readings is what contention was contributing.
"""

import threading


def before(n):
    lock = threading.Lock()
    total = 0
    for i in range(n):
        with lock:
            value = (i * 7919) % 10_007          # computed inside the lock
            total += value
    return total


def after(n):
    lock = threading.Lock()
    total = 0
    for i in range(n):
        value = (i * 7919) % 10_007              # computed outside
        with lock:
            total += value
    return total


def cases():
    return [("large",  lambda: (400_000,)),
            ("normal", lambda: (4_000,)),
            ("edge",   lambda: (0,))]
