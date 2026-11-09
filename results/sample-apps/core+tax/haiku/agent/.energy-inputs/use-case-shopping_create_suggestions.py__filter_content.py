# Inputs for use-case-shopping/create_suggestions.py::filter_content, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

_WORDS = [
    "wireless", "bluetooth", "headphones", "noise", "cancellation", "premium",
    "gaming", "laptop", "organic", "coffee", "beans", "stainless", "steel",
    "water", "bottle", "running", "shoes", "for", "men", "women", "kids",
    "smart", "watch", "fitness", "tracker", "portable", "charger", "usb",
    "cable", "fast", "charging", "desk", "lamp", "led", "adjustable",
    "ergonomic", "office", "chair", "memory", "foam", "pillow", "cotton",
    "bedsheets", "king", "size", "kitchen", "knife", "set", "ceramic",
    "plates", "dinnerware", "backpack", "travel", "leather", "wallet",
    "sunglasses", "polarized", "yoga", "mat", "resistance", "bands",
]


def _make(prefix, n, seed):
    rng = random.Random(seed)
    body = " ".join(rng.choice(_WORDS) for _ in range(n))
    return prefix + body


# Built once, at module level; the function never mutates its argument.
_NO_MATCH_SHORT = _make("", 3, 0)
_NO_MATCH_LONG = _make("", 5000, 1)
_NEAR_MISS = _make("anotherwise ", 400, 2)
_ONLY_LONG = _make("only ", 5000, 3)
_EITHER = _make("either ", 2000, 4)
_THE = _make("the ", 3000, 5)
_A = _make("a ", 4000, 6)
_MORE = _make("more ", 1000, 7)


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-char", lambda: ("a",)),
        ("none", lambda: (None,)),
    ]


def cases():
    return [
        ("no-match-short", lambda: (_NO_MATCH_SHORT,)),
        ("no-match-long", lambda: (_NO_MATCH_LONG,)),
        ("near-miss-another", lambda: (_NEAR_MISS,)),
        ("only-long-match", lambda: (_ONLY_LONG,)),
        ("either-match", lambda: (_EITHER,)),
        ("the-match", lambda: (_THE,)),
        ("a-match", lambda: (_A,)),
        ("more-match", lambda: (_MORE,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['near-miss-another', 'only-long-match', 'no-match-long', 'no-match-short']
_KEEP_CHECKS = ['empty', 'single-char', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
