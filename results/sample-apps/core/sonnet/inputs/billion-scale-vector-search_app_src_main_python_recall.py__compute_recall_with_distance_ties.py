# Inputs for billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random
import numpy as np

from recall import compute_recall_with_distance_ties


def _build(gt_size, count, tie_len, run_size, seed, hit_ratio=0.5):
    """Build one (true_ids, true_dists, run_ids, count) workload.

    true_dists is monotonic increasing (cumulative sum of positive steps);
    a run of equal values starting at index count-1 creates the distance tie
    the function is designed to detect.
    """
    rng = random.Random(seed)
    true_ids = np.array([rng.randrange(1, 10 ** 9) for _ in range(gt_size)],
                        dtype=np.int64)
    dists = np.cumsum(np.array([rng.random() for _ in range(gt_size)],
                               dtype=np.float64))

    tie_len = min(tie_len, gt_size - count + 1)
    if tie_len > 1:
        base = dists[count - 1]
        dists[count - 1:count - 1 + tie_len] = base

    run_ids = []
    for _ in range(run_size):
        if rng.random() < hit_ratio:
            run_ids.append(int(true_ids[rng.randrange(gt_size)]))
        else:
            run_ids.append(rng.randrange(1, 10 ** 9))

    return true_ids, dists, run_ids, count


# Built once, kept in memory; the function never mutates its arguments.
_CASE_DATA = [
    ("gt-eq-count",       _build(10,     10, 1,     100,  0)),
    ("no-tie-small",      _build(100,    10, 1,     50,   1)),
    ("tie-small",         _build(100,    10, 50,    100,  2)),
    ("tie-to-end-1k",     _build(1000,   10, 991,   200,  3)),
    ("count-100-tie-5k",  _build(5000,   100, 4901, 500,  4)),
    ("tie-to-end-20k",    _build(20000,  10, 19991, 1000, 5)),
    ("tie-to-end-50k",    _build(50000,  10, 49991, 1000, 6)),
    ("partial-tie-100k",  _build(100000, 10, 50000, 2000, 7)),
]


def cases():
    return [(label, (lambda a=args: a)) for label, args in _CASE_DATA]


def checks():
    return [
        ("empty",
         lambda: (np.array([], dtype=np.int64),
                  np.array([], dtype=np.float64),
                  [], 10)),
        ("single-eq-count",
         lambda: (np.array([7], dtype=np.int64),
                  np.array([0.5], dtype=np.float64),
                  [7], 1)),
        ("count-gt-size",
         lambda: (np.array([1, 2], dtype=np.int64),
                  np.array([0.1, 0.2], dtype=np.float64),
                  [1], 5)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['partial-tie-100k', 'tie-to-end-50k', 'tie-to-end-20k', 'count-100-tie-5k']
_KEEP_CHECKS = ['empty', 'single-eq-count', 'count-gt-size']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
