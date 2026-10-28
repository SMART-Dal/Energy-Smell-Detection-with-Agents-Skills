# Inputs for src/python/dxpy/utils/resolver.py::is_glob_pattern, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from dxpy.utils.resolver import is_glob_pattern


def _escaped_string(n_pairs, seed, chars="*?", max_letters=6):
    rng = random.Random(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    parts = []
    for _ in range(n_pairs):
        length = rng.randint(0, max_letters)
        if length:
            parts.append("".join(rng.choice(alphabet) for _ in range(length)))
        parts.append("\\" + rng.choice(chars))
    return "".join(parts)


# Pre-build every measured input once.  The function does not mutate strings.
_S1 = _escaped_string(2_000, 0, chars="*")
_S2 = _escaped_string(2_000, 1, chars="?")
_S3 = _escaped_string(4_000, 2, chars="*?")
_S4 = _escaped_string(5_000, 3, chars="*?", max_letters=10)
_S5 = "*" + _escaped_string(6_000, 4, chars="*")
_S6 = "?" + _escaped_string(6_000, 5, chars="?")
_S7 = _escaped_string(8_000, 6, chars="*?")
_S8 = _escaped_string(10_000, 7, chars="*?")


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-escaped-star", lambda: ("\\*",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("escaped-stars-2000", lambda: (_S1,)),
        ("escaped-questions-2000", lambda: (_S2,)),
        ("mixed-4000", lambda: (_S3,)),
        ("mixed-long-5000", lambda: (_S4,)),
        ("star-unescaped-start-6000", lambda: (_S5,)),
        ("question-unescaped-start-6000", lambda: (_S6,)),
        ("dense-mixed-8000", lambda: (_S7,)),
        ("very-dense-mixed-10000", lambda: (_S8,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['very-dense-mixed-10000', 'dense-mixed-8000', 'question-unescaped-start-6000', 'star-unescaped-start-6000']
_KEEP_CHECKS = ['empty', 'single-escaped-star', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
