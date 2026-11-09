# Inputs for news/src/python/metrics.py::ndcg_score, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random
import numpy as np

def _make(n, pos_ratio, seed, quantize=None):
    rng = random.Random(seed)
    y_true = np.fromiter((1 if rng.random() < pos_ratio else 0 for _ in range(n)),
                         dtype=np.int64, count=n)
    if quantize is not None:
        y_score = np.fromiter((rng.randrange(quantize) for _ in range(n)),
                              dtype=np.float64, count=n)
    else:
        y_score = np.fromiter((rng.random() for _ in range(n)),
                              dtype=np.float64, count=n)
    return y_true, y_score

_D1 = _make(1_000, 0.1, 0)
_D2 = _make(10_000, 0.1, 1)
_D3 = _make(100_000, 0.05, 2)
_D4 = _make(100_000, 0.1, 3)
_D5 = _make(300_000, 0.02, 4)
_D6 = _make(50_000, 0.1, 5, quantize=5)
_D7 = _make(20_000, 0.5, 6)
_D8 = _make(50_000, 0.2, 7)

def checks():
    return [
        ("empty", lambda: (np.array([]), np.array([]), 10)),
        ("single", lambda: (np.array([1]), np.array([0.5]), 10)),
        ("all-zero-labels", lambda: (np.array([0, 0, 0, 0]), np.array([0.1, 0.2, 0.3, 0.4]), 2)),
    ]

def cases():
    return [
        ("small-1k-k10", lambda: (_D1[0], _D1[1], 10)),
        ("medium-10k-k10", lambda: (_D2[0], _D2[1], 10)),
        ("large-100k-k10", lambda: (_D3[0], _D3[1], 10)),
        ("large-100k-k100", lambda: (_D4[0], _D4[1], 100)),
        ("xlarge-300k-k10", lambda: (_D5[0], _D5[1], 10)),
        ("ties-50k-k10", lambda: (_D6[0], _D6[1], 10)),
        ("high-pos-20k-k10", lambda: (_D7[0], _D7[1], 10)),
        ("k-gt-n-50k", lambda: (_D8[0], _D8[1], 100_000)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['xlarge-300k-k10', 'large-100k-k100', 'large-100k-k10', 'k-gt-n-50k']
_KEEP_CHECKS = ['empty', 'single', 'all-zero-labels']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
