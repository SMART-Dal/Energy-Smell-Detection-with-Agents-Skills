# Inputs for scripts/generate-sponsorship-ledger.py::rank_gc, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import importlib
import random

rank_gc = importlib.import_module('generate-sponsorship-ledger').rank_gc


def _mk(keys, lengths):
    # The function only inspects len(value); cheap zero-filled lists keep memory low.
    return dict(zip(keys, ([0] * l for l in lengths)))


_rng = random.Random(0)

# case 1: typical load, many keys, small varying list sizes
_keys1 = [f"gc-{i:06d}" for i in range(8000)]
_rng.shuffle(_keys1)
_c1 = _mk(_keys1, [random.Random(0).randrange(0, 10) for _ in range(8000)])

# case 2: everything ties on length -> heavy key comparison
_keys2 = [f"sig-{i:06d}" for i in range(30000)]
_rng.shuffle(_keys2)
_c2 = _mk(_keys2, [4] * 30000)

# case 3: all values empty (maximal length ties, all len 0)
_keys3 = [f"empty-{i:06d}" for i in range(30000)]
_rng.shuffle(_keys3)
_c3 = _mk(_keys3, [0] * 30000)

# case 4: power-law distribution, most tiny, a few very long
_rng4 = random.Random(1)
_keys4 = [f"pl-{i:06d}" for i in range(20000)]
_rng4.shuffle(_keys4)
_len4 = []
for i in range(20000):
    if _rng4.random() < 0.10:
        _len4.append(_rng4.randrange(200, 2000))
    else:
        _len4.append(_rng4.randrange(0, 4))
_c4 = _mk(_keys4, _len4)

# case 5: wide spread of moderate lengths
_rng5 = random.Random(2)
_keys5 = [f"wide-{i:05d}" for i in range(3000)]
_rng5.shuffle(_keys5)
_c5 = _mk(_keys5, [_rng5.randrange(0, 500) for _ in range(3000)])

# case 6: adversarial order (keys descending, lengths cycling in small range)
_keys6 = [f"adv-{i:06d}" for i in range(40000)]
_keys6.sort(reverse=True)
_c6 = _mk(_keys6, [i % 8 for i in range(40000)])

# case 7: large dictionary, random small lengths
_rng7 = random.Random(3)
_keys7 = [f"big-{i:06d}" for i in range(60000)]
_rng7.shuffle(_keys7)
_c7 = _mk(_keys7, [_rng7.randrange(0, 21) for _ in range(60000)])

# case 8: integer keys, medium lengths, mixed lengths
_rng8 = random.Random(4)
_keys8 = list(range(50000))
_rng8.shuffle(_keys8)
_c8 = _mk(_keys8, [_rng8.randrange(0, 51) for _ in range(50000)])


def checks():
    return [
        ("empty",      lambda: ({},)),
        ("single",     lambda: ({"only": [1, 2, 3]},)),
        ("none-value", lambda: ({"a": None, "b": [1]},)),
    ]


def cases():
    return [
        ("typical-8k",   lambda: (_c1,)),
        ("all-ties-30k", lambda: (_c2,)),
        ("all-empty-30k", lambda: (_c3,)),
        ("powerlaw-20k", lambda: (_c4,)),
        ("wide-lengths", lambda: (_c5,)),
        ("adversarial-40k", lambda: (_c6,)),
        ("big-60k",      lambda: (_c7,)),
        ("int-keys-50k", lambda: (_c8,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['big-60k', 'int-keys-50k', 'all-empty-30k', 'all-ties-30k']
_KEEP_CHECKS = ['empty', 'single', 'none-value']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
