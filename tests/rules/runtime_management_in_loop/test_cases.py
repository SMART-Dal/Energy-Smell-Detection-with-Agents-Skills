"""Cases for runtime_management_in_loop."""

import gc


def process_all(batches):
    # A full collection per batch: cost scales with the heap, not the batch.
    for batch in batches:
        handle(batch)
        gc.collect()


def reindex(groups):
    # The same inside a comprehension.
    return [gc.collect() or summarise(g) for g in groups]


def load_once(paths):
    # Collected once after the whole run, which is a deliberate decision.
    for path in paths:
        handle(path)
    gc.collect()


def before_fork(command):
    # The documented reason to force one: a compacted heap before forking.
    gc.collect()
    gc.freeze()
    return spawn(command)


def collect_results(batches):
    # `collect` on an ordinary object is not the garbage collector.
    out = []
    for batch in batches:
        out.append(batch.collect())
    return out
