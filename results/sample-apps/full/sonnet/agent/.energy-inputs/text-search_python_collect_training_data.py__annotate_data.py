# Inputs for text-search/python/collect_training_data.py::annotate_data, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

def _base(n, nf, seed, start=1000):
    rng = random.Random(seed)
    return [
        (start + i, {f"rf{j}": rng.uniform(-5.0, 5.0) for j in range(nf)})
        for i in range(n)
    ]

def _case(base, qid, rel):
    def thunk():
        # fresh copies every call: annotate_data mutates each rankfeatures dict
        return (
            [{"fields": {"id": i, "rankfeatures": dict(rf)}} for i, rf in base],
            qid,
            rel,
        )
    return thunk

# module-level data, built once
_B1 = _base(800, 20, 1)      # ids 1000..1799
_B2 = _base(4000, 12, 2)     # ids 1000..4999
_B3 = _base(150, 200, 3)     # ids 1000..1149
_B4 = _base(1200, 40, 4)     # ids 1000..2199
_B5 = _base(300, 60, 5)      # ids 1000..1299
_B6 = _base(2500, 16, 6)     # ids 1000..3499
_B7 = _base(600, 80, 7)      # ids 1000..1599
_B8 = _base(5000, 8, 8)      # ids 1000..5999


def checks():
    return [
        ("empty", lambda: ([], 1, 1)),
        ("single-relevant",
         lambda: ([{"fields": {"id": 7, "rankfeatures": {"rf0": 1.0}}}], 3, 7)),
        ("single-not-relevant",
         lambda: ([{"fields": {"id": 8, "rankfeatures": {"rf0": 0.5, "rf1": 2.0}}}], 4, 7)),
    ]


def cases():
    return [
        ("typical-800x20", _case(_B1, 100, 1000)),
        ("many-hits-4000x12", _case(_B2, 200, 999999)),
        ("wide-150x200", _case(_B3, 7, 1000)),
        ("relevant-first-1200x40", _case(_B4, 33, 1000)),
        ("no-relevant-300x60", _case(_B5, 501, 999999)),
        ("mid-2500x16", _case(_B6, 64, 1500)),
        ("dense-600x80", _case(_B7, 999, 1000)),
        ("large-5000x8", _case(_B8, 12345, 5999)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['large-5000x8', 'many-hits-4000x12', 'relevant-first-1200x40', 'typical-800x20']
_KEEP_CHECKS = ['empty', 'single-relevant', 'single-not-relevant']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
