"""C11.S3 Leaked Background Threads -- advisory; a worker with no shutdown path."""

import threading


def before(n):
    done = []

    def work():
        total = 0
        for i in range(n):
            total += i
        done.append(total)

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return len(done)


def after(n):
    done = []

    def work():
        total = 0
        for i in range(n):
            total += i
        done.append(total)

    threads = [threading.Thread(target=work, daemon=True) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return len(done)


def cases():
    return [("many-workers", lambda: (100_000,)), ("brief", lambda: (100,))]
