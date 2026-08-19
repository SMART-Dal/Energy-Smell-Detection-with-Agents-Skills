"""C12.S2 Sparse Element Access -- scattered indices into a buffer that fits in
cache.

The card's first `NOT a smell when` clause: scattered access inside a resident
array is free, because every line is already there. The repair is the same sort
that lost by 126% on a 20-million-element array, and here it should lose by
more and for a different reason -- there were no misses to avoid at all.
"""

import numpy as np


def before(values, indices):
    return float(values[indices].sum())


def after(values, indices):
    return float(values[np.sort(indices)].sum())


def _data():
    rng = np.random.default_rng(99)
    values = np.arange(20_000, dtype=np.float64)          # 160 KB, resident
    indices = rng.integers(0, 20_000, size=200_000)
    return values, indices


_VALUES, _INDICES = _data()


def cases():
    return [("resident", lambda: (_VALUES, _INDICES.copy())),
            ("small",    lambda: (_VALUES, _INDICES[:2_000].copy())),
            ("edge",     lambda: (_VALUES, _INDICES[:1].copy()))]
