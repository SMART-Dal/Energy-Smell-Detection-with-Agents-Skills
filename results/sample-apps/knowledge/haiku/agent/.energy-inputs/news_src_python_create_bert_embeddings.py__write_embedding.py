# Inputs for news/src/python/create_bert_embeddings.py::write_embedding, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import io
import random


def _normal(n, seed):
    rng = random.Random(seed)
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def _mixed_magnitudes(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.15:
            out.append(rng.uniform(-1e-8, 1e-8))
        elif r < 0.30:
            out.append(rng.uniform(-1e8, 1e8))
        elif r < 0.45:
            out.append(float(rng.randrange(-10**9, 10**9)) / 10**7)
        elif r < 0.55:
            out.append(0.0)
        else:
            out.append(rng.uniform(-1.0, 1.0))
    return out


_SPECIAL = [
    0.0, -0.0, 1.0, -1.0,
    0.00005, -0.00005, 0.000049999, -0.000049999,
    1e-8, -1e-8, 1e8, -1e8,
    12345.67895, -0.12345, 0.99995, 3.14159265,
]


def _special(n):
    return [_SPECIAL[i % len(_SPECIAL)] for i in range(n)]


_E1 = _normal(768, 0)
_E2 = _special(768)
_E3 = _normal(4096, 1)
_E4 = _normal(8192, 2)
_E5 = _normal(16384, 3)
_E6 = _normal(32768, 4)
_E7 = _normal(50000, 5)
_E8 = _mixed_magnitudes(20000, 6)


def checks():
    return [
        ("empty", lambda: (io.StringIO(), [])),
        ("single", lambda: (io.StringIO(), [0.123456])),
        ("none-value", lambda: (io.StringIO(), [None])),
    ]


def cases():
    return [
        ("bert-768", lambda: (io.StringIO(), _E1)),
        ("special-768", lambda: (io.StringIO(), _E2)),
        ("normal-4096", lambda: (io.StringIO(), _E3)),
        ("normal-8192", lambda: (io.StringIO(), _E4)),
        ("normal-16384", lambda: (io.StringIO(), _E5)),
        ("normal-32768", lambda: (io.StringIO(), _E6)),
        ("normal-50000", lambda: (io.StringIO(), _E7)),
        ("mixed-magnitudes-20000", lambda: (io.StringIO(), _E8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['normal-50000', 'normal-32768', 'mixed-magnitudes-20000', 'normal-16384']
_KEEP_CHECKS = ['empty', 'single', 'none-value']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
