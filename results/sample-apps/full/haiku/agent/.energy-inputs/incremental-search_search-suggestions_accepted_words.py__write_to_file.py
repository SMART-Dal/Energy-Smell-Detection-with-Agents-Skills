# Inputs for incremental-search/search-suggestions/accepted_words.py::write_to_file, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

import accepted_words
from accepted_words import write_to_file

# The function writes to the module-level global `file_name`; point it under WORKDIR.
_OUT_PATH = WORKDIR / "out" / "sub" / "accepted_words.txt"
accepted_words.file_name = str(_OUT_PATH)

_LOWER = "abcdefghijklmnopqrstuvwxyz"
_LOWER_DIGIT = "abcdefghijklmnopqrstuvwxyz0123456789"
_MIXED = "abcdefghijklmnopqrstuvwxyz0123456789_.- "
_UNICODE = "áéíóúñüçßåøæœàèìòùâêîôûäëïö主人公中文日本語한국어"


def _gen(n, seed, minlen, maxlen, alphabet):
    """A set of n distinct terms drawn from `alphabet`, with lengths in range."""
    rng = random.Random(seed)
    out = set()
    while len(out) < n:
        length = rng.randint(minlen, maxlen)
        out.add("".join(rng.choice(alphabet) for _ in range(length)))
    return out


# All data is built once, at module level; thunks only hand it back.
_TINY = _gen(500, 1, 3, 10, _LOWER)
_MEDIUM = _gen(20_000, 2, 3, 10, _LOWER)
_LARGE = _gen(60_000, 3, 3, 10, _LOWER)
_LONG_WORDS = _gen(3_000, 4, 150, 400, _LOWER)
_HUGE_WORDS = _gen(5_000, 5, 300, 800, _LOWER)
_UNICODE_WORDS = _gen(15_000, 6, 2, 12, _UNICODE)
_SHORT_TOKENS = _gen(8_000, 7, 1, 4, _LOWER_DIGIT)
_MIXED = _gen(30_000, 8, 2, 20, _MIXED)


def checks():
    return [
        ("empty", lambda: (set(),)),
        ("single", lambda: ({"hello"},)),
        ("odd-none", lambda: ({None},)),
    ]


def cases():
    return [
        ("tiny-500", lambda: (_TINY,)),
        ("medium-20k", lambda: (_MEDIUM,)),
        ("large-60k", lambda: (_LARGE,)),
        ("long-words", lambda: (_LONG_WORDS,)),
        ("huge-words", lambda: (_HUGE_WORDS,)),
        ("unicode", lambda: (_UNICODE_WORDS,)),
        ("short-tokens", lambda: (_SHORT_TOKENS,)),
        ("mixed-punct", lambda: (_MIXED,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['huge-words', 'large-60k', 'mixed-punct', 'unicode']
_KEEP_CHECKS = ['empty', 'single', 'odd-none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
