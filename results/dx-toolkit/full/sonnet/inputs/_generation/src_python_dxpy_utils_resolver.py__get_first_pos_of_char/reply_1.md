```python
import random

from dxpy.utils.resolver import get_first_pos_of_char

_FILLER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"


def _dense(char, gap, length, seed):
    """A string of roughly `length` chars in which `char` occurs every `gap` chars."""
    rng = random.Random(seed)
    out = []
    total = 0
    while total < length:
        out.append("".join(rng.choice(_FILLER) for _ in range(gap - 1)))
        out.append(char)
        total += gap
    return "".join(out)


def _escaped(char, reps, seed, weights):
    """`reps` occurrences of `char`, each preceded by a random number of backslashes.

    weights maps a backslash count to its sampling weight.
    """
    rng = random.Random(seed)
    pool = []
    for k, w in weights.items():
        pool.extend([k] * w)
    out = []
    for _ in range(reps):
        out.append("".join(rng.choice(_FILLER) for _ in range(3)))
        out.append("\\" * rng.choice(pool))
        out.append(char)
    return "".join(out)


def _glob_path(seed, segments):
    """A long glob-like path with many '*' and '?' wildcards."""
    rng = random.Random(seed)
    parts = []
    for i in range(segments):
        parts.append("f%d" % i)
        parts.append(rng.choice(["*", "*", "?", "x", "*"]))
    return "/".join(parts)


_STARS = _dense("*", 3, 12000, 0)
_QUESTIONS = _dense("?", 4, 16000, 1)
_EQUALS = _dense("=", 5, 20000, 2)
_COLONS = _dense(":", 6, 24000, 3)
_ALL_ESCAPED = _escaped("*", 4000, 4, {1: 1, 3: 1})
_MIXED = _escaped("*", 4000, 5, {0: 1, 1: 1, 2: 1, 3: 1})
_MOSTLY_ESCAPED = _escaped("*", 4000, 6, {0: 1, 1: 9})
_GLOB = _glob_path(7, 3000)


def checks():
    return [
        ("empty-string", lambda: ('*', "")),
        ("escaped-only", lambda: ('*', r"\*")),
        ("none-char", lambda: (None, "abc")),
    ]


def cases():
    return [
        ("stars-dense", lambda: ('*', _STARS)),
        ("questions-dense", lambda: ('?', _QUESTIONS)),
        ("equals-dense", lambda: ('=', _EQUALS)),
        ("colons-dense", lambda: (':', _COLONS)),
        ("all-escaped-stars", lambda: ('*', _ALL_ESCAPED)),
        ("mixed-escapes", lambda: ('*', _MIXED)),
        ("mostly-escaped", lambda: ('*', _MOSTLY_ESCAPED)),
        ("glob-path", lambda: ('*', _GLOB)),
    ]
```