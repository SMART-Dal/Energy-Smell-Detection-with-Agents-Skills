"""Cases for redundant_materialisation."""

import os

import numpy as np


def total_size(entries):
    # `sum` walks any iterable; the list is allocated, read once and dropped.
    return sum(list(entry.size for entry in entries))


def render_row(cells):
    # `str.join` takes an iterable and immediately materialises it, and
    # `PySequence_Fast` hands a list straight back, so the conversion is free:
    # 0.1928 ms against 0.1927 ms at 2000 elements. There is no allocation here
    # to remove, unlike `sorted(list(...))`, which really does copy.
    return " | ".join(list(map(str, cells)))


def ranked_names(records):
    # `sorted` builds a list of its own, so the inner one is a wasted copy.
    return sorted(list(r.name for r in records))


def summarise(results):
    # Two conversions, two findings; `any` also stops before it reads them all.
    failed = any(list(r.failed for r in results))
    worst = max(list(r.severity for r in results))
    return failed, worst


def pair_scores(names, scores):
    # `zip` consumes every argument lazily, not only the first one.
    return dict(zip(names, list(scores)))


def make_totaller(field):
    # The conversion belongs to the closure, not to the factory around it.
    def total(records):
        return sum(list(getattr(r, field) for r in records))

    return total


def band_energy(spectrum, bands):
    # `np.sum` is not the builtin: handed a generator it builds a 0-d object
    # array instead of a total, so the list is what makes this correct.
    return np.sum(list(spectrum[lo:hi].max() for lo, hi in bands))


def missing_dependencies(wanted, available):
    # `set.difference` has a fast path for a hashed argument, so it pays for itself.
    return set(wanted).difference(set(available))


def average_latency(samples):
    # Bound and read twice: the conversion is what makes the second read work.
    values = list(samples)
    return sum(values) / len(values)


def join_path_parts(parts):
    # Deliberately out of scope: `os.path.join(...)` is this exact shape and
    # does not take an iterable, so a module-path receiver is never trusted.
    return os.sep.join(list(parts))


def uniq_in_order(items):
    # Already lazy: there is no conversion left to delete.
    return list(dict.fromkeys(item for item in items if item))


def total_and_count(rows):
    # The sequence is consumed twice; a generator is empty by the second.
    sizes = list(len(row) for row in rows)
    return sum(sizes), len(sizes)


def pick_optimal(candidate_a, candidate_b):
    # Two arguments to `min` are two values being compared, not one sequence
    # being walked. Dropping the conversions raises TypeError rather than
    # saving an allocation.
    return min(list(candidate_a), list(candidate_b))


def flush_pending(active_queue):
    # The conversion is the only reason this loop is correct: it snapshots a
    # collection the body then shrinks.
    for idx, task in enumerate(list(active_queue)):
        if task.is_expired():
            active_queue.remove(task)
