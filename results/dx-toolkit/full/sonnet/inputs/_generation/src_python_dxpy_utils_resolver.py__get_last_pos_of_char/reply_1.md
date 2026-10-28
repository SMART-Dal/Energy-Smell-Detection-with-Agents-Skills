```python
import random

from dxpy.utils.resolver import get_last_pos_of_char


def _mixed(n, seed):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.25:
            out.append('/')
        elif r < 0.45:
            out.append('\\')
        else:
            out.append(rng.choice('abcdefgh'))
    return ''.join(out)


_rng = random.Random(0)

# A realistic, fairly deep project folder path (many unescaped slashes).
_LONG_PATH = "/" + "/".join(
    "dir%d_%s" % (i, "".join(_rng.choice("abcdefghijklmnop") for _ in range(6)))
    for i in range(1500)
) + "/file.txt"

_SHORT_PATH = "/home/user/data/file.txt"

# Every slash is escaped by a single backslash -> the function walks back
# through all of them.
_ESCAPED_ALL = "\\/" * 9000

# Escaped slashes separated by long filler runs: each iteration copies a
# large prefix.
_GAPPED_ESCAPED = "".join("a" * 50 + "\\/" for _ in range(2000))

# Escaped slashes with random-length filler between them.
_grng = random.Random(7)
_GAPPED_RANDOM = "".join("a" * _grng.randint(0, 30) + "\\/" for _ in range(3000))

# Random mix of slashes, backslashes and letters.
_MIXED = _mixed(60000, 1)

# No occurrence at all in a large string.
_NO_OCC = "a" * 300000

# Colon-separated path where every colon is escaped.
_COLON_ESCAPED = "proj" + "\\:" * 5000


def checks():
    return [
        ("empty-string", lambda: ('/', "")),
        ("single-char", lambda: ('/', "/")),
        ("char-absent", lambda: ('/', "abcdef")),
    ]


def cases():
    return [
        ("short-path", lambda: ('/', _SHORT_PATH)),
        ("long-path", lambda: ('/', _LONG_PATH)),
        ("all-escaped-slashes", lambda: ('/', _ESCAPED_ALL)),
        ("gapped-escaped", lambda: ('/', _GAPPED_ESCAPED)),
        ("gapped-random-escaped", lambda: ('/', _GAPPED_RANDOM)),
        ("mixed-random", lambda: ('/', _MIXED)),
        ("no-occurrence", lambda: ('/', _NO_OCC)),
        ("escaped-colons", lambda: (':', _COLON_ESCAPED)),
    ]
```