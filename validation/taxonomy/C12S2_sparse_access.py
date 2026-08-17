"""C12.S2 Sparse Element Access -- scattered indices against sorted ones.

Same elements, same count, different visit order: the only variable is
locality.
"""

import numpy as np


def before(a, idx):
    return float(a[idx].sum())


def after(a, idx):
    return float(a[np.sort(idx)].sum())


def cases():
    rng = np.random.default_rng(1234)
    big = np.arange(20_000_000, dtype=np.float64)
    scattered = rng.integers(0, 20_000_000, size=2_000_000)
    return [("scattered", lambda: (big, scattered.copy())),
            ("tiny", lambda: (big[:1000].copy(), np.array([5, 1, 900])))]
