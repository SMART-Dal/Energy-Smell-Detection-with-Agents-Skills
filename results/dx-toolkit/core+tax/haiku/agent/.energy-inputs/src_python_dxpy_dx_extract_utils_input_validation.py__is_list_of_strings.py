# Inputs for src/python/dxpy/dx_extract_utils/input_validation.py::is_list_of_strings, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random
import string


def _strings(n, seed, length=8):
    rng = random.Random(seed)
    return ["".join(rng.choices(string.ascii_letters, k=length)) for _ in range(n)]


def _mixed(n, seed, bad_index, bad_value):
    rng = random.Random(seed)
    items = ["".join(rng.choices(string.ascii_letters, k=8)) for _ in range(n)]
    items[bad_index] = bad_value
    return items


# module-level, built once; thunks just return the (immutable enough) data
_ALL_200K = _strings(200_000, 0)
_ALL_100K_LONG = _strings(100_000, 1, length=60)
_BAD_END = _strings(150_000, 2) + [12345]
_BAD_START = [None] + _strings(150_000, 3)
_BAD_MID = _mixed(150_000, 4, 75_000, {"not": "a string"})
_TUPLE = tuple(_strings(50_000, 5))
_DICT = {i: "x" for i in range(50_000)}
_EMPTY = []


def checks():
    return [
        ("empty-list",        lambda: ([],)),
        ("single-string",     lambda: (["rs123"],)),
        ("single-nonstring",  lambda: ([1],)),
    ]


def cases():
    return [
        ("all-strings-200k",   lambda: (_ALL_200K,)),
        ("all-strings-100k-long", lambda: (_ALL_100K_LONG,)),
        ("nonstring-at-end",   lambda: (_BAD_END,)),
        ("nonstring-at-start", lambda: (_BAD_START,)),
        ("nonstring-in-middle", lambda: (_BAD_MID,)),
        ("tuple-input",        lambda: (_TUPLE,)),
        ("dict-input",         lambda: (_DICT,)),
        ("empty-list",         lambda: (_EMPTY,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['all-strings-200k', 'nonstring-at-end', 'all-strings-100k-long', 'nonstring-in-middle']
_KEEP_CHECKS = ['empty-list', 'single-string', 'single-nonstring']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
