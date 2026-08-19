"""C12.S2 Sparse Element Access -- compact once, then read the subset many
times.

The other C12.S2 case sorts the indices for a single gather and loses by 126%,
because the sort costs more than the misses it avoids. The card says the
repair pays when the reordering amortises across many passes, so this one does
the gather `passes` times. `one-pass` and `many-passes` put the amortisation on
either side, which is the only way to say where it turns.
"""

import numpy as np


def before(values, indices, passes):
    total = 0.0
    for _ in range(passes):
        total += float(values[indices].sum())
    return round(total, 3)


def after(values, indices, passes):
    compact = values[indices]            # paid once
    total = 0.0
    for _ in range(passes):
        total += float(compact.sum())
    return round(total, 3)


def _data():
    rng = np.random.default_rng(1234)
    values = np.arange(20_000_000, dtype=np.float64)
    indices = rng.integers(0, 20_000_000, size=500_000)
    return values, indices


_VALUES, _INDICES = _data()


def cases():
    return [("many-passes", lambda: (_VALUES, _INDICES.copy(), 20)),
            ("one-pass",    lambda: (_VALUES, _INDICES.copy(), 1)),
            ("edge",        lambda: (_VALUES, _INDICES[:1].copy(), 1))]
