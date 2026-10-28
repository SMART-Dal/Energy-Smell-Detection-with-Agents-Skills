# Inputs for test/pseudo_terminal.py::Log.write, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
from pseudo_terminal import Log

def _make_log(pattern, verbose):
    log = Log()
    log._filter_pattern = pattern
    log._verbose = verbose
    return log

def _random_chars(n, seed):
    rng = random.Random(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    return "".join(rng.choices(alphabet, k=n))

_LARGE_0 = _random_chars(500_000, 0)
_LARGE_1 = _random_chars(500_000, 1)
_LARGE_2 = _random_chars(500_000, 2)
_LARGE_4 = _random_chars(100_000, 4)
_A_500K = "a" * 500_000
_A_500K_BANG = _A_500K + "!"
_UPPER_500K_B = "A" * 500_000 + "b"
_A_22_BANG = "a" * 22 + "!"
_A1_11_BANG = "a1" * 11 + "!"

def checks():
    return [
        ("empty-string", lambda: (_make_log("", False), "")),
        ("none-string", lambda: (_make_log("", False), None)),
        ("none-pattern", lambda: (_make_log(None, False), "test")),
    ]

def cases():
    return [
        ("dot-star-match", lambda: (_make_log("^.*$", False), _LARGE_0)),
        ("prefix-dot-star", lambda: (_make_log("^PASS.*", False), "PASS " + _LARGE_1)),
        ("uppercase-backtrack", lambda: (_make_log("^[A-Z]+$", False), _UPPER_500K_B)),
        ("charclass-backtrack", lambda: (_make_log("^[a-z0-9_]+$", False), _A_500K_BANG)),
        ("charclass-match", lambda: (_make_log("^[a-z0-9_]+$", False), _A_500K)),
        ("exp-nested-quantifier", lambda: (_make_log("^([a-z]+)+$", False), _A_22_BANG)),
        ("verbose-scan-write", lambda: (_make_log("^FAIL.*[0-9]$", True), "FAIL " + _LARGE_4 + "x")),
        ("exp-charclass-plus", lambda: (_make_log("^([a-z0-9]+)+$", False), _A1_11_BANG)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['exp-charclass-plus', 'exp-nested-quantifier', 'uppercase-backtrack', 'charclass-backtrack']
_KEEP_CHECKS = ['empty-string', 'none-string', 'none-pattern']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
