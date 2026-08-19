"""C11.S5 Missed Parallelism -- CPU-bound work across processes.

The card's central claim and the one it says must be reported honestly: for
I/O-bound work energy falls with time, and for CPU-bound work there is no idle
to reclaim, so wall time falls while total energy is flat or worse. A process
pool is the only way to parallelise CPU-bound Python at all.

If this reads as a time saving and an energy loss, that is the card being right
and is more valuable than a confirmation -- it is direct evidence for "energy
is not time", which is one of the things the whole project claims.
"""

from concurrent.futures import ProcessPoolExecutor

WORKERS = 4


def _work(n):
    total = 0
    for i in range(n):
        total += (i * 7919) % 10_007
    return total


def before(tasks, work):
    return sum(_work(work) for _ in range(tasks))


def after(tasks, work):
    with ProcessPoolExecutor(WORKERS) as pool:
        return sum(pool.map(_work, [work] * tasks))


def cases():
    # Deliberately modest. `after` spins up a pool per call, and the harness
    # repeats each call until its window lasts about a second -- so a large
    # per-call cost multiplies into hundreds of process spawns and a timeout.
    return [("many-tasks", lambda: (8, 60_000)),
            ("few-tasks",  lambda: (2, 60_000)),
            ("edge",       lambda: (1, 500))]
