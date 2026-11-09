```python
import random
from collections import OrderedDict
from backend.cache import LRUCache

_rng = random.Random(0)


def _build_cache(n, key_func):
    c = LRUCache(max_size=n)
    for i in range(n):
        c.cache[key_func(i)] = _rng.randint(0, 10**9)
    return c


_TINY = _build_cache(10, lambda i: f"key{i}")
_SMALL = _build_cache(100, lambda i: f"key{i}")
_MEDIUM = _build_cache(10_000, lambda i: f"key{i}")
_LARGE = _build_cache(50_000, lambda i: f"key{i}")
_INT = _build_cache(10_000, lambda i: i)
_TUPLE = _build_cache(10_000, lambda i: (i, i % 10))

_LONG_LEN = 2_000_000
_LONG_N = 20


def _long_key(i):
    return f"longkey{i}_" + "x" * _LONG_LEN


_LONG = _build_cache(_LONG_N, _long_key)


def _copy(template):
    inst = LRUCache(max_size=template.max_size)
    inst.cache = OrderedDict(template.cache)
    return inst


def checks():
    single = LRUCache(max_size=1)
    single.cache["only"] = 42
    return [
        ("empty-cache", lambda: (LRUCache(), "missing")),
        ("single-entry", lambda: (single, "only")),
        ("unhashable-key", lambda: (LRUCache(), [1, 2, 3])),
    ]


def cases():
    return [
        ("tiny-hit", lambda: (_copy(_TINY), "key5")),
        ("tiny-miss", lambda: (_copy(_TINY), "missing")),
        ("medium-hit-front", lambda: (_copy(_MEDIUM), "key0")),
        ("medium-hit-back", lambda: (_copy(_MEDIUM), "key9999")),
        ("large-hit-middle", lambda: (_copy(_LARGE), "key25000")),
        ("large-miss", lambda: (_copy(_LARGE), "notfound")),
        ("int-keys-hit", lambda: (_copy(_INT), 5000)),
        ("long-string-keys-hit", lambda: (_copy(_LONG), _long_key(10))),
    ]
```