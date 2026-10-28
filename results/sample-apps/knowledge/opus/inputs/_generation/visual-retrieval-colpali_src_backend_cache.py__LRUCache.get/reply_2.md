```python
import random
from collections import OrderedDict

from backend.cache import LRUCache


def _build(n, key_of, seed=0):
    c = LRUCache(max_size=max(n, 1))
    rng = random.Random(seed)
    for i in range(n):
        c.cache[key_of(i)] = rng.randint(0, 10 ** 9)
    return c


def _halves(n):
    return "a" * n, "b" * n


_A250, _B250 = _halves(125_000)
_A500, _B500 = _halves(250_000)
_A1M, _B1M = _halves(500_000)
_A2M, _B2M = _halves(1_000_000)

_KEY250 = _A250 + _B250
_KEY500 = _A500 + _B500
_KEY1M = _A1M + _B1M
_KEY2M = _A2M + _B2M


def _cache_with_long(n_short, tag, long_key, seed):
    c = LRUCache(max_size=n_short + 1)
    rng = random.Random(seed)
    for i in range(n_short):
        c.cache[f"{tag}{i}"] = rng.randint(0, 10 ** 9)
    c.cache[long_key] = rng.randint(0, 10 ** 9)
    return c


_C5_250 = _cache_with_long(4, "p", _KEY250, 1)
_C5_500 = _cache_with_long(4, "q", _KEY500, 2)
_C20_500 = _cache_with_long(19, "r", _KEY500, 3)
_C100_1M = _cache_with_long(99, "s", _KEY1M, 4)
_C5_2M = _cache_with_long(4, "t", _KEY2M, 5)

_MISS5 = _build(5, lambda i: f"m{i}", 6)
_MISS20 = _build(20, lambda i: f"n{i}", 7)
_MISS100 = _build(100, lambda i: f"o{i}", 8)

_ONE = LRUCache(max_size=1)
_ONE.cache["only"] = 7


def checks():
    return [
        ("empty", lambda: (LRUCache(), "x")),
        ("single-hit", lambda: (_ONE, "only")),
        ("unhashable", lambda: (LRUCache(), [1, 2, 3])),
    ]


def cases():
    return [
        ("hit-250k-small", lambda: (_C5_250, _A250 + _B250)),
        ("hit-500k-small", lambda: (_C5_500, _A500 + _B500)),
        ("miss-500k-small", lambda: (_MISS5, _A500 + _B500)),
        ("hit-500k-medium", lambda: (_C20_500, _A500 + _B500)),
        ("miss-500k-medium", lambda: (_MISS20, _A500 + _B500)),
        ("hit-1m-large", lambda: (_C100_1M, _A1M + _B1M)),
        ("miss-1m-large", lambda: (_MISS100, _A1M + _B1M)),
        ("hit-2m-small", lambda: (_C5_2M, _A2M + _B2M)),
    ]
```