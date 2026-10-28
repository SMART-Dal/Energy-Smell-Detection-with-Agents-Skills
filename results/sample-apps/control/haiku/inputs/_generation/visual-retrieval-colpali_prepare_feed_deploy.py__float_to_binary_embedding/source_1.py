import random


def _embedding(n, dim, seed, positive_ratio=None):
    """Build a dict {patch_index: [float, ...]} like the ColPali embedding_dict."""
    rng = random.Random(seed)
    if positive_ratio is None:
        return {i: [rng.uniform(-1.0, 1.0) for _ in range(dim)] for i in range(n)}
    out = {}
    for i in range(n):
        row = []
        for _ in range(dim):
            if rng.random() < positive_ratio:
                row.append(rng.uniform(0.0, 1.0))
            else:
                row.append(rng.uniform(-1.0, 0.0))
        out[i] = row
    return out


# Built once, at module level; the function only reads its argument.
_TYPICAL = _embedding(1030, 128, 0)
_LARGE = _embedding(2048, 128, 1)
_DIM768 = _embedding(512, 768, 2)
_DIM64 = _embedding(3000, 64, 3)
_DIM1024 = _embedding(900, 1024, 4)
_MANY_PATCHES = _embedding(4096, 128, 5)
_SMALL = _embedding(32, 128, 6)
_SPARSE = _embedding(1500, 128, 7, positive_ratio=0.08)


def checks():
    return [
        ("empty-dict", lambda: ({},)),
        ("single-value", lambda: ({0: [1.0]},)),
        ("all-zeros", lambda: ({0: [0.0, 0.0, 0.0], 1: [0.0, 0.0, 0.0]},)),
    ]


def cases():
    return [
        ("colpali-typical-1030x128", lambda: (_TYPICAL,)),
        ("colpali-large-2048x128", lambda: (_LARGE,)),
        ("dim-768-512-patches", lambda: (_DIM768,)),
        ("dim-64-3000-patches", lambda: (_DIM64,)),
        ("dim-1024-900-patches", lambda: (_DIM1024,)),
        ("many-patches-4096x128", lambda: (_MANY_PATCHES,)),
        ("small-batch-32x128", lambda: (_SMALL,)),
        ("sparse-mostly-negative", lambda: (_SPARSE,)),
    ]
