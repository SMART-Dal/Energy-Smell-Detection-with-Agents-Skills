"""C11.S3 Unmanaged Thread Lifecycle -- a leaked poller that spins.

The card says what a leaked thread costs depends entirely on what it does while
it lives: a blocking wait costs memory only, a polling loop costs a lock
acquisition per poll, and a busy-wait costs a core. The other C11.S3 case leaks
threads that block, and read -0.1%. This one leaks threads that spin, which is
the form the card says is expensive -- so if there is any energy claim in this
root cause at all, it is here.
"""

import threading
import time

SPINNERS = 4


def _spin(stop, until):
    while not stop.is_set() and time.monotonic() < until:
        pass                                   # busy-wait: no sleep, no yield


def _work(n):
    total = 0
    for i in range(n):
        total += (i * 7919) % 10_007
    return total


def before(n, lifetime):
    stop = threading.Event()
    until = time.monotonic() + lifetime
    threads = [threading.Thread(target=_spin, args=(stop, until), daemon=True)
               for _ in range(SPINNERS)]
    for t in threads:
        t.start()
    result = _work(n)
    stop.set()                                 # only after the work is done
    for t in threads:
        t.join()
    return result


def after(n, lifetime):
    # The pollers are never started: the work does not need them.
    return _work(n)


def cases():
    return [("leaked",  lambda: (300_000, 0.5)),
            ("brief",   lambda: (300_000, 0.01)),
            ("edge",    lambda: (0, 0.01))]
