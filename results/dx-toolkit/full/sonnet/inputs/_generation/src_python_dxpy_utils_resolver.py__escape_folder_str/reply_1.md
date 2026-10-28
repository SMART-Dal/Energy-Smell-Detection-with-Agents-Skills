```python
import random

from dxpy.utils.resolver import escape_folder_str

_SPECIALS = "#?*: ;&`\"'!$(){}[]<>|~"
_ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _rand_chars(n, pool, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(pool, k=n))


def _plain(n, seed):
    return _rand_chars(n, _ALNUM, seed)


def _spaces(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_ALNUM + "     /", k=n))


def _backslashes(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_ALNUM + "\\" * 4, k=n))


def _all_specials(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_SPECIALS, k=n))


def _mixed(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_ALNUM + _SPECIALS + "\\", k=n))


def _dense(n, seed):
    rng = random.Random(seed)
    return "".join(rng.choices(_SPECIALS * 3 + _ALNUM, k=n))


def _unicode_mixed(n, seed):
    rng = random.Random(seed)
    pool = _ALNUM + _SPECIALS + "éüñ中文字Жλß"
    return "".join(rng.choices(pool, k=n))


def _realistic_paths(n, seed):
    rng = random.Random(seed)
    words = ["data", "raw", "results", "analysis", "sample", "run", "batch",
             "output", "project", "test", "v1", "v2", "2021", "cohort",
             "reads", "aligned", "fastq", "bam", "summary"]
    suffixes = [" (copy)", " [old]", " #1", " &more", " ~bak", "", ""]
    parts = []
    for _ in range(n):
        depth = rng.randint(1, 5)
        path = "/" + "/".join(rng.choice(words) for _ in range(depth))
        path += rng.choice(suffixes)
        parts.append(path)
    return "\n".join(parts)


_PLAIN = _plain(2_000_000, 0)
_SPACES = _spaces(600_000, 1)
_BACKSLASHES = _backslashes(400_000, 2)
_ALL_SPECIALS = _all_specials(400_000, 3)
_MIXED = _mixed(500_000, 4)
_DENSE = _dense(300_000, 5)
_UNICODE = _unicode_mixed(400_000, 6)
_PATHS = _realistic_paths(6000, 7)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-char", lambda: ("a",)),
        ("single-special", lambda: ("#",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("plain-alnum", lambda: (_PLAIN,)),
        ("spaces-and-slashes", lambda: (_SPACES,)),
        ("backslashes", lambda: (_BACKSLASHES,)),
        ("all-specials", lambda: (_ALL_SPECIALS,)),
        ("random-mixed", lambda: (_MIXED,)),
        ("dense-escapes", lambda: (_DENSE,)),
        ("unicode-mixed", lambda: (_UNICODE,)),
        ("realistic-paths", lambda: (_PATHS,)),
    ]
```