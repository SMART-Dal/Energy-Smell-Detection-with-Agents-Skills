```python
import random

from dxpy.dx_extract_utils.input_validation_somatic import is_list_of_strings


_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_UNI_ALPHA = "áéíóúàèìòùäöüßñç日"


def _strings(n, seed, alphabet=_ALPHA, minlen=1, maxlen=20):
    """Build n strings from a random character pool (fast, deterministic)."""
    rng = random.Random(seed)
    pool = "".join(rng.choices(alphabet, k=n * maxlen))
    out = []
    pos = 0
    for _ in range(n):
        k = rng.randint(minlen, maxlen)
        out.append(pool[pos:pos + k])
        pos += k
    return out


# Module-level inputs, built once and reused (setup is never timed).
_S_250K = _strings(250_000, 0)
_S_120K = _strings(120_000, 1)
_LONG = _strings(60_000, 2, minlen=60, maxlen=120)
_UNI = _strings(120_000, 3, alphabet=_UNI_ALPHA)
_EMPTY = [""] * 250_000
_END = _strings(150_000, 4) + [None]
_MID = _strings(120_000, 5)
_MID.insert(60_000, 12345)
_BYTES = _strings(120_000, 6) + [b"bytes"]


def checks():
    return [
        ("none",         lambda: (None,)),
        ("tuple",        lambda: (("a", "b"),)),
        ("empty-list",   lambda: ([],)),
    ]


def cases():
    return [
        ("all-strings-250k",     lambda: (_S_250K,)),
        ("all-strings-120k",     lambda: (_S_120K,)),
        ("long-strings-60k",     lambda: (_LONG,)),
        ("unicode-strings-120k", lambda: (_UNI,)),
        ("empty-strings-250k",   lambda: (_EMPTY,)),
        ("nonstr-at-end-150k",   lambda: (_END,)),
        ("nonstr-at-mid-120k",   lambda: (_MID,)),
        ("bytes-at-end-120k",    lambda: (_BYTES,)),
    ]
```