"""C11.S5 Missed Parallelism Opportunities -- independent blocking waits run serially.

Only a smell when the work releases the GIL. `sleep` does; pure Python
arithmetic does not, which is why the card's exception matters.
"""

import time
from concurrent.futures import ThreadPoolExecutor


def _wait(d):
    time.sleep(d)
    return 1


def before(n, delay):
    return sum(_wait(delay) for _ in range(n))


def after(n, delay):
    with ThreadPoolExecutor(max_workers=8) as pool:
        return sum(pool.map(_wait, [delay] * n))


def cases():
    return [("many-waits", lambda: (64, 0.01)), ("one-wait", lambda: (1, 0.01))]
