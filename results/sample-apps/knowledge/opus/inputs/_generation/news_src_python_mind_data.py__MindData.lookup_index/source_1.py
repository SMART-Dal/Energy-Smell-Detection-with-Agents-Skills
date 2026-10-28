import random

from mind_data import MindData

# The method under test never touches `self`; build a bare instance once.
_INST = MindData.__new__(MindData)


def _unique_keys(n, prefix, seed, width=8):
    rng = random.Random(seed)
    seen = set()
    while len(seen) < n:
        seen.add(f"{prefix}{rng.randrange(10 ** width):0{width}d}")
    return list(seen)


# --- large map of news ids, the way the repository fills news_map ---
_NEWS_KEYS = _unique_keys(50_000, "N", 0)
_NEWS_MAP = {k: i for i, k in enumerate(_NEWS_KEYS)}
_NEWS_HIT = _NEWS_KEYS[12345]
_NEWS_MISS = "X00000000"          # different prefix -> guaranteed absent

# --- tiny map (few users seen so far) ---
_SMALL_MAP = {f"U{i}": i for i in range(8)}
_SMALL_HIT = "U3"
_SMALL_MISS = "U99"

# --- integer-keyed map ---
_INT_MAP = {i: i for i in range(30_000)}
_INT_HIT = 12345
_INT_MISS = 10 ** 9

# --- long string keys (entity ids / long titles) ---
_LONG_KEYS = [f"{'q' * 199}{i}" for i in range(20_000)]
_LONG_MAP = {k: i for i, k in enumerate(_LONG_KEYS)}
_LONG_HIT = _LONG_KEYS[7777]
_LONG_MISS = "q" * 199 + "x"


def checks():
    return [
        ("empty-map", lambda: (_INST, "U1", {})),
        ("none-id", lambda: (_INST, None, {})),
        ("existing-key", lambda: (_INST, "x", {"x": 5})),
    ]


def cases():
    return [
        # large map, id already present -> pure lookup
        ("news-hit-large", lambda: (_INST, _NEWS_HIT, dict(_NEWS_MAP))),
        # large map, id absent -> insert into a fresh copy every call
        ("news-miss-large", lambda: (_INST, _NEWS_MISS, dict(_NEWS_MAP))),
        # tiny map, hit
        ("small-hit", lambda: (_INST, _SMALL_HIT, dict(_SMALL_MAP))),
        # tiny map, miss
        ("small-miss", lambda: (_INST, _SMALL_MISS, dict(_SMALL_MAP))),
        # empty map, miss -> index 0 assigned
        ("empty-miss", lambda: (_INST, "U0", {})),
        # integer keys, hit
        ("int-hit", lambda: (_INST, _INT_HIT, dict(_INT_MAP))),
        # integer keys, miss
        ("int-miss", lambda: (_INST, _INT_MISS, dict(_INT_MAP))),
        # very long string keys, hit
        ("long-key-hit", lambda: (_INST, _LONG_HIT, dict(_LONG_MAP))),
    ]
