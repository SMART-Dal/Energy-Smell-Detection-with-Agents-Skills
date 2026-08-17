"""C1.S8 Excessive Runtime-Management Calls -- gc.collect() inside a loop."""

import gc


def before(batches):
    total = 0
    for b in batches:
        total += sum(b)
        gc.collect()
    return total


def after(batches):
    total = 0
    for b in batches:
        total += sum(b)
    return total


def cases():
    return [("many-batches", lambda: ([[1, 2, 3]] * 300,)),
            ("few-batches", lambda: ([[1, 2, 3]] * 5,))]
