# Inputs for use-case-shopping/create_suggestions.py::filter, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

_WORDS = [
    "organic", "cotton", "shirt", "blue", "summer", "dress", "women",
    "men", "kids", "shoes", "leather", "handbag", "wool", "sweater",
    "jacket", "denim", "jeans", "sneakers", "boots", "sandals",
    "vintage", "slim", "fit", "casual", "formal", "party", "wedding",
    "beach", "sport", "running", "training", "yoga", "gym", "winter",
    "spring", "autumn", "floral", "striped", "plain", "printed",
]


def _long_clean(rng, target):
    """Build a letters-and-spaces string of exactly `target` chars.

    Contains no character/substring from the module's `filters` set, so the
    loop in `filter` has to scan every filter entry.
    """
    s = ""
    while len(s) < target:
        w = rng.choice(_WORDS)
        s = w if not s else s + " " + w
    return s[:target]


_rng = random.Random(0)

# 1/2: clean strings -> full scan over all filters, returns False.
_C1 = _long_clean(_rng, 64)
_C2 = _long_clean(_rng, 40)

# 3: filter character right at the start (";" is the first filter) -> early True.
_C3 = ";" + _long_clean(_rng, 40)

# 4: "5." near the very end -> hit only after almost the whole loop.
_C4 = _long_clean(_rng, 60) + "5."

# 5/6: numeric filters "191" / "24" appended to otherwise clean text.
_C5 = _long_clean(_rng, 55) + " 191"
_C6 = _long_clean(_rng, 55) + " 24"

# 7: punctuation-heavy text with several filter characters.
_C7 = _long_clean(_rng, 30) + " (" + _long_clean(_rng, 20) + ")"

# 8: over-length text -> immediate True without entering the loop.
_C8 = _long_clean(_rng, 64) * 2


def checks():
    return [
        ("empty",       lambda: ("",)),      # len < 3 -> True
        ("single-char", lambda: ("a",)),     # len < 3 -> True
        ("none",        lambda: (None,)),    # len(None) raises
    ]


def cases():
    return [
        ("clean-64-full-scan", lambda: (_C1,)),
        ("clean-40-full-scan", lambda: (_C2,)),
        ("hit-first-filter",   lambda: (_C3,)),
        ("hit-late-filter",    lambda: (_C4,)),
        ("numeric-191",        lambda: (_C5,)),
        ("numeric-24",         lambda: (_C6,)),
        ("punctuation-mix",    lambda: (_C7,)),
        ("over-length",        lambda: (_C8,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['hit-late-filter', 'clean-40-full-scan', 'clean-64-full-scan', 'numeric-191']
_KEEP_CHECKS = ['empty', 'single-char', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
