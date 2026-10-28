# Inputs for incremental-search/search-suggestions/count_terms.py::count_terms, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

from count_terms import count_terms


# ---------------------------------------------------------------------------
# Input builders (setup only -- never timed)
# ---------------------------------------------------------------------------

def _words(n, vocab_size, seed, prefix="w"):
    """A realistic document: a list of words drawn from a small vocabulary."""
    rng = random.Random(seed)
    return [f"{prefix}{rng.randrange(vocab_size)}" for _ in range(n)]


def _unique_words(n, prefix="u"):
    """A document where every word is distinct (worst case for term counts)."""
    return [f"{prefix}{i}" for i in range(n)]


def _common(vocab_size, count, seed, prefix="w"):
    rng = random.Random(seed)
    return {f"{prefix}{i}" for i in rng.sample(range(vocab_size), count)}


# Documents / common-word sets are built once, at module level.
_D1 = _words(5_000, 800, 1)
_C1 = set()

_D2 = _words(6_000, 1_500, 2)
_C2 = _common(1_500, 50, 2)

_D3 = _words(10_000, 2_000, 3)
_C3 = _common(2_000, 100, 3)

_D4 = _words(8_000, 1_200, 4)
_C4 = _common(1_200, 200, 4)

_D5 = _words(6_000, 1_000, 5)
_C5 = _common(1_000, 300, 5)

_D6 = _unique_words(6_000)
_C6 = set()

# Very small vocabulary + most of it marked common -> high short-circuit ratio.
_D7 = _words(8_000, 300, 7)
_C7 = _common(300, 250, 7)

_D8 = _words(20_000, 3_000, 8)
_C8 = _common(3_000, 100, 8)


# ---------------------------------------------------------------------------
# Edge cases -- checked only, never measured
# ---------------------------------------------------------------------------

def checks():
    return [
        ("empty-doc", lambda: ([],)),
        ("single-word", lambda: (["hello"],)),
        ("string-doc", lambda: ("hello world",)),
    ]


# ---------------------------------------------------------------------------
# Measured cases
# ---------------------------------------------------------------------------

def cases():
    return [
        ("unigrams-medium", lambda: (_D1, 1, _C1)),
        ("bigrams", lambda: (_D2, 2, _C2)),
        ("trigrams-long", lambda: (_D3, 3, _C3)),
        ("fourgrams", lambda: (_D4, 4, _C4)),
        ("fivegrams", lambda: (_D5, 5, _C5)),
        ("all-unique-trigrams", lambda: (_D6, 3, _C6)),
        ("common-heavy-trigrams", lambda: (_D7, 3, _C7)),
        ("large-unigrams", lambda: (_D8, 1, _C8)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['trigrams-long', 'fourgrams', 'fivegrams', 'all-unique-trigrams']
_KEEP_CHECKS = ['empty-doc', 'single-word', 'string-doc']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
