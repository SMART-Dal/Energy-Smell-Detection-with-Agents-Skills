# Inputs for news/src/python/mind_data.py::MindData.lookup_news_index, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import itertools
import random

from mind_data import MindData

# ---------------------------------------------------------------------------
# Setup (never timed): build MindData instances that only carry a news_map,
# which is the single attribute lookup_news_index -> lookup_index reads.
# ---------------------------------------------------------------------------

_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _instance(news_map):
    inst = MindData.__new__(MindData)
    inst.news_map = news_map
    return inst


def _random_string(length, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_ALPHABET, k=length))


# realistic MIND news ids ("N27209", "N12345", ...)
_NUM_NEWS = 60_000
_BASE_MAP = {f"N{i:06d}": i for i in range(_NUM_NEWS)}

# long ids that are present in the map: hashing the id dominates the lookup
_LONG_LENGTHS = (32, 512, 4_000, 16_000, 64_000, 100_000)
_LONG_KEYS = {}
for _i, _length in enumerate(_LONG_LENGTHS):
    _key = _random_string(_length, 1000 + _length)
    _LONG_KEYS[_length] = _key
    _BASE_MAP[_key] = _NUM_NEWS + _i

_SHARED_INSTANCE = _instance(_BASE_MAP)

# small map used for miss cases (a fresh copy per call keeps every call a miss)
_SMALL_MAP = {f"N{i:06d}": i for i in range(500)}
_SMALL_INSTANCE = _instance(_SMALL_MAP)

_MISS_SHORT = "N500000"
_MISS_LONG = _random_string(80_000, 7)


# Does lookup_index create an entry when the id is absent?  Probe once, at
# import time, so that miss cases are only generated when they cannot raise.
def _detect_insertion():
    try:
        _instance({}).lookup_news_index("N000001")
        return True
    except Exception:
        return False


_INSERTS = _detect_insertion()


def _hit_thunk(instance, key):
    return lambda: (instance, key)


def _miss_thunk(key):
    def thunk():
        return (_instance(dict(_SMALL_MAP)), key)
    return thunk


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def checks():
    return [
        ("empty-map-empty-id", lambda: (_instance({}), "")),
        ("single-entry-hit", lambda: (_instance({"N000001": 0}), "N000001")),
        ("none-id", lambda: (_instance({"N000001": 0}), None)),
    ]


def cases():
    hit_short = ("hit-short-big-map", _hit_thunk(_SHARED_INSTANCE, "N000123"))
    hit_small = ("hit-short-small-map", _hit_thunk(_SMALL_INSTANCE, "N000123"))
    hit_len = {
        L: (f"hit-{L}-chars", _hit_thunk(_SHARED_INSTANCE, _LONG_KEYS[L]))
        for L in _LONG_LENGTHS
    }

    if _INSERTS:
        return [
            hit_short,
            hit_len[32],
            hit_len[4_000],
            hit_len[16_000],
            hit_len[64_000],
            hit_len[100_000],
            ("miss-short-id", _miss_thunk(_MISS_SHORT)),
            ("miss-long-id", _miss_thunk(_MISS_LONG)),
        ]

    return [
        hit_short,
        hit_len[32],
        hit_len[512],
        hit_len[4_000],
        hit_len[16_000],
        hit_len[64_000],
        hit_len[100_000],
        hit_small,
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['hit-64000-chars', 'hit-100000-chars', 'hit-short-big-map', 'hit-32-chars']
_KEEP_CHECKS = ['empty-map-empty-id', 'single-entry-hit', 'none-id']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
