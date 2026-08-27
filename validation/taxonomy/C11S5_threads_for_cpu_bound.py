"""C11.S5 Missed Parallelism Opportunities -- threads for
CPU-bound work.

The description names this outright -- "a common Python mistake is using threads
for CPU-bound work and wondering why it is not faster" -- and
`C11S5_missed_parallelism` measures a thread pool over `time.sleep` at +86.4%,
because `sleep` releases the interpreter lock.

Pure Python arithmetic does not. The eight workers here take turns holding the
GIL, so the wall time is what it was serially plus the scheduling, and the
energy is what it was plus eight thread stacks, the pool, and a context switch
every few milliseconds. The code is now concurrent and does strictly more work.

The question is what the work releases the GIL for: I/O, `time.sleep`, a numpy
call, a C extension that unlocks. Where the answer is "nothing", the parallelism
that was missed is a `ProcessPoolExecutor` -- and that one has to pay for
pickling the arguments, which is `C11S5_transfer_dominates`.
"""

from concurrent.futures import ThreadPoolExecutor

WORKERS = 8


def _work(n):
    total = 0
    for i in range(n):
        total += (i * 7919) % 10_007
    return total


def before(tasks, work):
    return sum(_work(work) for _ in range(tasks))


def after(tasks, work):
    with ThreadPoolExecutor(WORKERS) as pool:
        return sum(pool.map(_work, [work] * tasks))


def cases():
    return [("many-tasks", lambda: (32, 20_000)),
            ("one-task",   lambda: (1, 20_000)),
            ("edge",       lambda: (0, 10))]
