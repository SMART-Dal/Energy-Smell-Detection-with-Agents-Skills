import random

_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _rand_str(rng, minlen, maxlen):
    n = rng.randint(minlen, maxlen)
    return "".join(rng.choice(_ALPHABET) for _ in range(n))


def _str_pairs(n, seed, minlen=6, maxlen=18):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        s = _rand_str(rng, minlen, maxlen)
        if s in seen:
            continue
        seen.add(s)
        out.append((s, rng.randrange(10 ** 9)))
    return out


def _int_pairs(n, seed):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        k = rng.randrange(-(2 ** 62), 2 ** 62)
        if k in seen:
            continue
        seen.add(k)
        out.append((k, "v%d" % rng.randrange(10 ** 9)))
    return out


def _tuple_pairs(n, seed, width):
    rng = random.Random(seed)
    seen = set()
    out = []
    while len(out) < n:
        k = tuple(rng.randrange(10 ** 6) for _ in range(width))
        if k in seen:
            continue
        seen.add(k)
        out.append((k, rng.random()))
    return out


def _mixed_pairs(n, seed):
    rng = random.Random(seed)
    out = []
    per = n // 7 + 1
    for j in range(per):
        out.append(("s%d_%s" % (j, _rand_str(rng, 4, 10)), j))
    for j in range(per):
        out.append((rng.randrange(2 ** 62), j))
    for j in range(per):
        out.append((float(j) + 0.5, j))
    for j in range(per):
        out.append((b"b%d" % j, j))
    for j in range(per):
        out.append(((str(j), str(j * 7 + 1)), j))
    for j in range(per):
        out.append((frozenset((j, j + 1)), j))
    out.append((None, "none"))
    return out[:n]


# Module-level data: built once, reused by every timed call (the function only reads it).
_STR_90K = _str_pairs(90_000, 11)
_INT_90K = _int_pairs(90_000, 12)
_TUP_60K = _tuple_pairs(60_000, 13, 3)
_MIXED_70K = _mixed_pairs(70_000, 14)
_LIST_90K = [list(p) for p in _str_pairs(90_000, 15)]
_LONG_50K = _str_pairs(50_000, 16, 60, 120)
_NESTED_50K = _tuple_pairs(50_000, 17, 6)
_SMALL_20K = _str_pairs(20_000, 18)


def checks():
    return [
        ("empty", lambda: ([],)),
        ("single", lambda: ([("only", 1)],)),
        ("duplicate", lambda: ([("a", 1), ("b", 2), ("a", 3)],)),
    ]


def cases():
    return [
        ("strings-90k", lambda: (_STR_90K,)),
        ("ints-90k", lambda: (_INT_90K,)),
        ("tuples-60k", lambda: (_TUP_60K,)),
        ("mixed-types-70k", lambda: (_MIXED_70K,)),
        ("list-pairs-90k", lambda: (_LIST_90K,)),
        ("long-keys-50k", lambda: (_LONG_50K,)),
        ("nested-tuples-50k", lambda: (_NESTED_50K,)),
        ("small-20k", lambda: (_SMALL_20K,)),
    ]
