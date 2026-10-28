# Inputs for src/python/dxpy/utils/spelling_corrector.py::_edits1, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from dxpy.utils.spelling_corrector import _edits1


def _rand_word(n, seed, alphabet="abcdefghijklmnopqrstuvwxyz"):
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(n))


# Build all words once, at module level (setup is never timed).
_W5 = _rand_word(5, 0)
_W12 = _rand_word(12, 1)
_W25 = _rand_word(25, 2)
_W50_SMALL = _rand_word(50, 3, "abc")
_W90 = _rand_word(90, 4)
_W150 = _rand_word(150, 5)
_W260 = _rand_word(260, 6)
_W400_MIXED = _rand_word(
    400, 7,
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-char", lambda: ("a",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("word-5", lambda: (_W5,)),
        ("word-12", lambda: (_W12,)),
        ("word-25", lambda: (_W25,)),
        ("word-50-small-alphabet", lambda: (_W50_SMALL,)),
        ("word-90", lambda: (_W90,)),
        ("word-150", lambda: (_W150,)),
        ("word-260", lambda: (_W260,)),
        ("word-400-mixed", lambda: (_W400_MIXED,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['word-400-mixed', 'word-260', 'word-150', 'word-90']
_KEEP_CHECKS = ['empty', 'single-char', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
