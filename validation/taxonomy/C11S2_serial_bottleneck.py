"""C11.S2 Forced Serial Bottleneck -- one lock serialising independent work."""

import threading


def _run(worker):
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return True


def before(n):
    lock = threading.Lock()

    def worker():
        for i in range(n):
            with lock:                      # global lock, nothing shared
                _ = (i * 7919) % 10_007
    return _run(worker)


def after(n):
    locks = [threading.Lock() for _ in range(4)]
    counter = [0]

    def worker():
        mine = locks[counter[0] % 4]
        counter[0] += 1
        for i in range(n):
            with mine:
                _ = (i * 7919) % 10_007
    return _run(worker)


def cases():
    return [("contended", lambda: (60_000,)), ("brief", lambda: (200,))]
