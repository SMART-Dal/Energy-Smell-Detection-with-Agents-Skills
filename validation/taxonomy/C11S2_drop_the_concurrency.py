"""C11.S2 Forced Serial Bottleneck -- removing the concurrency altogether.

The card says this is often the right repair and this measures it: when
everything serialises anyway, a plain loop does the same work without forking,
scheduling or handing the interpreter lock around. The comparison is a thread
pool whose tasks are CPU-bound Python -- which cannot parallelise -- against
the same work done serially.
"""

from concurrent.futures import ThreadPoolExecutor

WORKERS = 8


def _work(n):
    total = 0
    for i in range(n):
        total += (i * 7919) % 10_007
    return total


def before(tasks, work):
    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(_work, [work] * tasks))


def after(tasks, work):
    return sum(_work(work) for _ in range(tasks))


def cases():
    return [("many-tasks", lambda: (400, 3_000)),
            ("few-tasks",  lambda: (8, 3_000)),
            ("edge",       lambda: (0, 10))]
