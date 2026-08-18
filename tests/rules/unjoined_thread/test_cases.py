"""Cases for unjoined_thread."""

import threading
from concurrent.futures import ThreadPoolExecutor


def spawn_worker(job):
    # Started and never joined; nothing bounds how long it runs.
    worker = threading.Thread(target=run, args=(job,))
    worker.start()
    return worker


def fan_out(jobs):
    # One per job, none joined.
    for job in jobs:
        threading.Thread(target=run, args=(job,)).start()


def spawn_and_wait(job):
    # Joined in the same unit.
    worker = threading.Thread(target=run, args=(job,))
    worker.start()
    worker.join()


def pooled(jobs):
    # The context manager shuts the pool down on exit.
    with ThreadPoolExecutor(4) as pool:
        pool.map(run, jobs)


def start_a_timer(seconds):
    # A join elsewhere in the unit is enough for the rule to stay quiet.
    timer = threading.Timer(seconds, run)
    timer.start()
    timer.join(timeout=1)
