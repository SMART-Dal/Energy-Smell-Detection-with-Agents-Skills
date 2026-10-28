# Inputs for news/src/python/mind_data.py::MindData.lookup_index, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from mind_data import MindData

# The method under test never uses `self`, so build a bare instance once.
# (Using __new__ avoids the file-reading __init__.)
_INST = MindData.__new__(MindData)


def _unique_keys(n, prefix, seed, width=8):
    rng = random.Random(seed)
    seen = set()
    while len(seen) < n:
        seen.add(f"{prefix}{rng.randrange(10 ** width):0{width}d}")
    return list(seen)


# --- shared maps, reused by reference for the "hit" cases (a hit never mutates) ---
_NEWS_KEYS = _unique_keys(50_000, "N", 0)
_NEWS_MAP = {k: i for i, k in enumerate(_NEWS_KEYS)}
_NEWS_HIT = _NEWS_KEYS[12345]

_SMALL_MAP = {f"U{i}": i for i in range(8)}
_SMALL_HIT = "U3"

_INT_MAP = {i: i for i in range(30_000)}
_INT_HIT = 12345

_LONG_KEYS = [f"{'q' * 199}{i}" for i in range(20_000)]
_LONG_MAP = {k: i for i, k in enumerate(_LONG_KEYS)}
_LONG_HIT = _LONG_KEYS[7777]

# keys used for the "miss" cases (absent from the fresh maps below)
_MISS_NEWS = "X00000000"
_MISS_INT = 10 ** 9
_MISS_LONG = "q" * 199 + "x"
_MISS_SMALL = "U99"

# tiny maps that are cheap to rebuild on every call
_TINY_MAP = {"a": 0, "b": 1, "c": 2}


def checks():
    return [
        ("empty-map", lambda: (_INST, "U1", {})),
        ("none-id", lambda: (_INST, None, {})),
        ("existing-key", lambda: (_INST, "x", {"x": 5})),
    ]


def cases():
    return [
        # --- hits: reuse the shared map by reference, so the thunk is free ---
        ("news-hit-large", lambda: (_INST, _NEWS_HIT, _NEWS_MAP)),
        ("small-hit", lambda: (_INST, _SMALL_HIT, _SMALL_MAP)),
        ("int-hit", lambda: (_INST, _INT_HIT, _INT_MAP)),
        ("long-key-hit", lambda: (_INST, _LONG_HIT, _LONG_MAP)),
        # --- misses: fresh cheap maps, every call inserts into its own dict ---
        ("news-miss-empty", lambda: (_INST, _MISS_NEWS, {})),
        ("small-miss-tiny", lambda: (_INST, _MISS_SMALL, dict(_TINY_MAP))),
        ("int-miss-empty", lambda: (_INST, _MISS_INT, {})),
        ("long-key-miss", lambda: (_INST, _MISS_LONG, {})),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['int-miss-empty', 'long-key-miss', 'news-miss-empty', 'small-miss-tiny']
_KEEP_CHECKS = ['empty-map', 'none-id', 'existing-key']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
