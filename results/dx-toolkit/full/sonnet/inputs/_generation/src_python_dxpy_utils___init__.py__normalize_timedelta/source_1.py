import random

from dxpy.utils import normalize_timedelta


def _digits(n, seed):
    """A long, non-uniform decimal string (no leading zero) of length n."""
    rng = random.Random(seed)
    return str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(n - 1))


# Built once at module level; thunks just hand the same string back.
_PLAIN = _digits(3200, 0)
_NEG = "-" + _digits(3000, 1)
_S = _digits(3100, 2) + "s"
_M = _digits(2900, 3) + "m"
_H = _digits(3300, 4) + "h"
_D = _digits(3000, 5) + "d"
_W = _digits(2700, 6) + "w"
_Y = _digits(3200, 7) + "y"


def checks():
    return [
        ("empty", lambda: ("",)),
        ("bad-suffix", lambda: ("10x",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("plain-seconds", lambda: (_PLAIN,)),
        ("plain-negative", lambda: (_NEG,)),
        ("suffix-s", lambda: (_S,)),
        ("suffix-m", lambda: (_M,)),
        ("suffix-h", lambda: (_H,)),
        ("suffix-d", lambda: (_D,)),
        ("suffix-w", lambda: (_W,)),
        ("suffix-y", lambda: (_Y,)),
    ]
